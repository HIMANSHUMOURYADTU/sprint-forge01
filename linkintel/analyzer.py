"""
analyzer.py - deterministic internal-linking + topical-authority analysis from a
Screaming Frog export (internal_html.csv + all_inlinks.csv + all_outlinks.csv +
all_anchor_text.csv + a page text/ folder).
"""
from __future__ import annotations
import csv, os, re, math
from collections import defaultdict, Counter
from urllib.parse import urlparse
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

csv.field_size_limit(10_000_000)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
GENERIC_ANCHORS = {
    "click here", "read more", "read more...", "learn more", "more", "here",
    "this", "this page", "link", "view more", "see more", "details", "more details",
    "know more", "discover more", "find out more", "continue reading", "go",
    "click", "view", "see details", "more info", "info",
}

STOPWORDS = set("""a an the and or but if then else for to of in on at by with from as is are was were be been being this that these those it its we you they he she them our your their i me my mine our ours us not no yes do does did doing have has had having will would can could should may might must shall about into over under again further once here there all any both each few more most other some such only own same so than too very s t can just don now get got also into out up down off above below""".split())

# --------------------------------------------------------------------------- #
# Parsing Helpers
# --------------------------------------------------------------------------- #
def _int(v, d=0):
    try:
        return int(float(str(v).strip()))
    except Exception:
        return d

def _norm(u: str) -> str:
    """Normalise a URL for matching (drop trailing slash, fragment)."""
    if not u:
        return ""
    u = u.split("#")[0].strip()
    if len(u) > 1 and u.endswith("/"):
        u = u[:-1]
    return u

def is_html(r):  return "text/html" in (r.get("Content Type", "") or "").lower()
def is_200(r):   return _int(r.get("Status Code")) == 200
def indexable(r): return (r.get("Indexability", "") or "").strip().lower() == "indexable"

def load_pages(export_dir: str) -> list[dict]:
    for name in ("internal_html.csv", "internal_all.csv"):
        p = os.path.join(export_dir, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))
    raise FileNotFoundError("internal_html.csv / internal_all.csv not found in export dir")

def load_links(export_dir: str, fname="all_inlinks.csv") -> list[dict]:
    p = os.path.join(export_dir, fname)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def load_page_text(export_dir: str) -> dict:
    out = {}
    folder = None
    for cand in ("page text", "page_text", "pagetext"):
        d = os.path.join(export_dir, cand)
        if os.path.isdir(d):
            folder = d
            break
    if not folder:
        return out
    from urllib.parse import unquote
    for fn in os.listdir(folder):
        if not fn.endswith(".txt"):
            continue
        stem = fn[:-4]
        stem = re.sub(r"^original_", "", stem)
        stem = stem.replace("https_", "https://", 1).replace("http_", "http://", 1)
        if "://" in stem:
            scheme, rest = stem.split("://", 1)
            rest = rest.replace("_", "/")
            url = f"{scheme}://{rest}"
        else:
            url = stem.replace("_", "/")
        url = unquote(url)
        try:
            with open(os.path.join(folder, fn), encoding="utf-8", errors="ignore") as f:
                out[_norm(url)] = f.read()
        except Exception:
            pass
    return out

# --------------------------------------------------------------------------- #
# Text Analysis Helpers
# --------------------------------------------------------------------------- #
def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z][a-z0-9\-]{2,}", (text or "").lower())
            if w not in STOPWORDS]

def page_keywords(page, body: str, top=12) -> list[str]:
    blob = " ".join([
        page.get("Title 1", "") or "", (page.get("H1-1", "") or "") + " ",
        page.get("H2-1", "") or "", page.get("H2-2", "") or "", (body or "")[:6000],
    ])
    c = Counter(_tokens(blob))
    return [w for w, _ in c.most_common(top)]

def _get_semantic_blob(page, body: str) -> str:
    return " ".join([
        page.get("Title 1", "") or "",
        page.get("H1-1", "") or "",
        page.get("H2-1", "") or "",
        page.get("H2-2", "") or "",
        (body or "")[:5000]
    ])

def _find_optimal_k(embeddings, n_samples):
    min_k = 5
    max_k = min(30, n_samples // 4)
    if max_k < min_k:
        return max(1, n_samples // 10) if n_samples > 1 else 1
    best_k = min_k
    best_score = -1.0
    for k in range(min_k, max_k + 1):
        if k < 2 or k >= n_samples:
            continue
        try:
            clusterer = AgglomerativeClustering(n_clusters=k).fit(embeddings)
            score = silhouette_score(embeddings, clusterer.labels_)
            if score > best_score:
                best_score = score
                best_k = k
        except Exception:
            continue
    return best_k

def _clean_phrase(text: str) -> str:
    if not text:
        return ""
    text = re.split(r'\||-', text)[0]
    text = re.sub(r'http\S+|www\S+|<.*?>', '', text)
    text = " ".join(text.lower().split())
    words = text.split()
    if not words:
        return ""
    return " ".join(words[:6])

def _generate_anchor(target_page: dict, shared_topics: list[str], target_keywords: list[str]) -> str:
    h1 = _clean_phrase(target_page.get("H1-1", ""))
    if h1 and len(h1.split()) >= 2:
        return h1
    title = _clean_phrase(target_page.get("Title 1", ""))
    if title and len(title.split()) >= 2:
        return title
    if shared_topics:
        shared = _clean_phrase(" ".join(shared_topics[:2]))
        if shared and len(shared.split()) >= 2:
            return shared
    if target_keywords:
        kws = _clean_phrase(" ".join(target_keywords[:2]))
        if kws and len(kws.split()) >= 2:
            return kws
    return title or "internal resource"

# --------------------------------------------------------------------------- #
# Core Analysis
# --------------------------------------------------------------------------- #
def build_graph(pages, inlinks):
    page_set = {_norm(p["Address"]) for p in pages}
    out_adj = defaultdict(set)
    in_adj = defaultdict(set)
    follow_in = defaultdict(int)
    for r in inlinks:
        if r.get("Type") != "Hyperlink":
            continue
        s = _norm(r.get("Source", ""))
        d = _norm(r.get("Destination", ""))
        if not s or not d or s == d:
            continue
        if d not in page_set:
            continue
        out_adj[s].add(d)
        in_adj[d].add(s)
        if (r.get("Follow", "true") or "true").strip().lower() == "true":
            follow_in[d] += 1
    return {"page_set": page_set, "out": out_adj, "in": in_adj, "follow_in": follow_in}

def graph_stats(pages, inlinks, graph) -> dict:
    idx200 = [p for p in pages if is_html(p) and is_200(p) and indexable(p)]
    by_url = {_norm(p["Address"]): p for p in pages}
    orphans = sorted(_norm(p["Address"]) for p in idx200 if _int(p.get("Unique Inlinks")) == 0)
    depth = {_norm(p["Address"]): _int(p.get("Crawl Depth")) for p in idx200}
    maxd = max(depth.values()) if depth else 0
    deepest = sorted([u for u, d in depth.items() if d == maxd])
    inl = {_norm(p["Address"]): _int(p.get("Unique Inlinks")) for p in idx200}
    UNDER = 1
    under_linked = sorted([u for u, n in inl.items() if n <= UNDER])
    vals = sorted(inl.values())
    over_thresh = vals[int(len(vals) * 0.95)] if vals else 0
    over_linked = sorted([u for u, n in inl.items() if n >= max(over_thresh, 1) and n == max(vals or [0])][:0]) \
        or sorted([u for u, n in inl.items() if over_thresh and n >= over_thresh])
    broken, redir, nofollow = [], [], []
    for r in inlinks:
        sc = _int(r.get("Status Code"))
        typ = r.get("Type", "")
        dst = _norm(r.get("Destination", ""))
        src = _norm(r.get("Source", ""))
        if typ == "Hyperlink" and 400 <= sc <= 599:
            broken.append({"source": src, "destination": dst, "status": sc, "anchor": (r.get("Anchor", "") or "").strip()})
        if typ == "Hyperlink" and 300 <= sc <= 399:
            redir.append({"source": src, "destination": dst, "status": sc, "anchor": (r.get("Anchor", "") or "").strip()})
        if typ == "Hyperlink" and (r.get("Follow", "true") or "").strip().lower() == "false":
            nofollow.append({"source": src, "destination": dst, "anchor": (r.get("Anchor", "") or "").strip()})
    return {
        "pages_total": len(pages),
        "pages_indexable": len(idx200),
        "internal_links": sum(len(v) for v in graph["out"].values()),
        "max_crawl_depth": maxd,
        "orphan_pages": orphans,
        "deepest_pages": deepest,
        "under_linked_pages": under_linked,
        "over_linked_pages": over_linked,
        "broken_internal_links": broken,
        "redirect_internal_links": redir,
        "nofollow_internal_links": nofollow,
        "avg_inlinks": round(sum(inl.values()) / len(inl), 1) if inl else 0,
    }

def anchor_analysis(inlinks) -> dict:
    hyper = [r for r in inlinks if r.get("Type") == "Hyperlink"]
    generic, empty = [], []
    dest_anchor = defaultdict(Counter)
    for r in hyper:
        a = (r.get("Anchor", "") or "").strip()
        al = a.lower()
        src = _norm(r.get("Source", ""))
        dst = _norm(r.get("Destination", ""))
        if not a:
            empty.append({"source": src, "destination": dst})
            continue
        if al in GENERIC_ANCHORS:
            generic.append({"source": src, "destination": dst, "anchor": a})
        dest_anchor[dst][al] += 1
    over = []
    for dst, ctr in dest_anchor.items():
        total = sum(ctr.values())
        if total < 10:
            continue
        anchor, cnt = ctr.most_common(1)[0]
        if anchor and anchor not in GENERIC_ANCHORS and cnt / total >= 0.6 and cnt >= 10:
            over.append({"destination": dst, "anchor": anchor, "count": cnt, "share": round(cnt / total, 2)})
    return {
        "generic_anchors": generic,
        "empty_or_image_only": empty,
        "over_optimized_anchors": sorted(over, key=lambda x: -x["count"]),
        "total_internal_anchors": len(hyper),
    }

def cluster_pages(pages, page_text, n_keywords=12) -> dict:
    idx200 = [p for p in pages if is_html(p) and is_200(p) and indexable(p)]
    if not idx200:
        return {"clusters": [], "page_keywords": {}, "embeddings": {}}
    urls = [_norm(p["Address"]) for p in idx200]
    model = SentenceTransformer('all-MiniLM-L6-v2')
    blobs = [_get_semantic_blob(p, page_text.get(_norm(p["Address"]), "")) for p in idx200]
    embeddings = model.encode(blobs)
    embeddings_dict = {url: emb for url, emb in zip(urls, embeddings)}
    n_samples = len(idx200)
    n_clusters = _find_optimal_k(embeddings, n_samples)
    clustering = AgglomerativeClustering(n_clusters=n_clusters).fit(embeddings)
    labels = clustering.labels_
    clusters_map = defaultdict(list)
    for url, label in zip(urls, labels):
        clusters_map[label].append(url)
    kw = {}
    for p in idx200:
        u = _norm(p["Address"])
        kw[u] = page_keywords(p, page_text.get(u, ""), n_keywords)
    out = []
    inl = {_norm(p["Address"]): _int(p.get("Unique Inlinks")) for p in idx200}
    for label in sorted(clusters_map.keys(), key=lambda l: -len(clusters_map[l])):
        members = sorted(clusters_map[label])
        hub = max(members, key=lambda u: inl.get(u, 0)) if members else None
        hub_inlinks = inl.get(hub, 0)
        member_inl = sorted((inl.get(m, 0) for m in members), reverse=True)
        clear_hub = bool(len(member_inl) >= 2 and hub_inlinks >= 2 * (member_inl[1] or 1))
        ck = Counter()
        for m in members:
            ck.update(kw.get(m, []))
        cluster_kws = [w for w, _ in ck.most_common(8)]
        name = " ".join([w.title() for w in cluster_kws[:2]]) if cluster_kws else "General Topic"
        out.append({
            "key": f"cluster_{label}",
            "name": name,
            "size": len(members),
            "pages": members,
            "hub_page": hub,
            "hub_inlinks": hub_inlinks,
            "authority": "hub" if clear_hub else "scattered",
            "keywords": cluster_kws,
        })
    return {"clusters": out, "page_keywords": kw, "embeddings": embeddings_dict}

def relatedness(embeddings_dict: dict, page_keywords: dict, top_per_page=50) -> dict:
    urls = list(embeddings_dict.keys())
    kw_sets = {u: set(page_keywords.get(u, [])) for u in urls}
    edges = {}
    for u in urls:
        scored = []
        vec_u = embeddings_dict[u]
        set_u = kw_sets[u]
        for v in urls:
            if v == u:
                continue
            vec_v = embeddings_dict[v]
            sim = np.dot(vec_u, vec_v) / (np.linalg.norm(vec_u) * np.linalg.norm(vec_v) + 1e-9)
            if sim < 0.15:
                continue
            set_v = kw_sets[v]
            shared_kws = sorted(list(set_u & set_v))[:6]
            scored.append((v, round(float(sim), 3), shared_kws))
        scored.sort(key=lambda x: -x[1])
        edges[u] = [{"to": v, "score": s, "shared": sh} for v, s, sh in scored[:top_per_page]]
    return edges

def link_candidates(graph, relate, pages, clusters, max_per_page=5) -> list:
    idx200 = [p for p in pages if is_html(p) and is_200(p) and indexable(p)]
    inl = {_norm(p["Address"]): _int(p.get("Unique Inlinks")) for p in idx200}
    url_to_page = {_norm(p["Address"]): p for p in idx200}
    page_to_cluster = {}
    for c in clusters.get("clusters", []):
        for p in c["pages"]:
            page_to_cluster[p] = c["key"]
    LOW_VALUE_PATTERNS = ["/author/", "/tag/", "/page/", "/archive/", "/category/"]
    HIGH_VALUE_PATTERNS = ["/services/", "/solutions/", "/case-studies/", "/guides/", "/resources/", "/industry/"]
    important = sorted(inl, key=lambda u: -inl[u])[:40]
    out = []
    for u in important:
        already = graph["out"].get(u, set())
        scored_candidates = []
        u_cluster = page_to_cluster.get(u)
        for e in relate.get(u, []):
            v = e["to"]
            if v in already or v == u:
                continue
            sem_score = e["score"]
            same_cluster = 1.0 if u_cluster and page_to_cluster.get(v) == u_cluster else 0.0
            underlinked = 1.0 if inl.get(v, 0) <= 1 else 0.0
            orphan = 1.0 if inl.get(v, 0) == 0 else 0.0
            high_value = 1.0 if any(pat in v.lower() for pat in HIGH_VALUE_PATTERNS) else 0.0
            low_value = 1.0 if any(pat in v.lower() for pat in LOW_VALUE_PATTERNS) else 0.0
            final_score = (
                0.45 * sem_score +
                0.20 * same_cluster +
                0.15 * underlinked +
                0.10 * orphan +
                0.15 * high_value -
                0.40 * low_value
            )
            scored_candidates.append({
                "target": v,
                "relate_score": e["score"],
                "shared": e["shared"],
                "final_score": final_score
            })
        scored_candidates.sort(key=lambda x: -x["final_score"])
        top_cands = []
        for c in scored_candidates[:max_per_page]:
            target_url = c["target"]
            target_page = url_to_page.get(target_url, {})
            shared_topics = c["shared"]
            target_keywords = clusters.get("page_keywords", {}).get(target_url, [])
            anchor = _generate_anchor(target_page, shared_topics, target_keywords)
            top_cands.append({
                "target": target_url,
                "relatedness": c["relate_score"],
                "shared_topics": shared_topics,
                "suggested_anchor": anchor
            })
        if top_cands:
            out.append({"source": u, "candidates": top_cands})
    return out

def analyze(export_dir: str) -> dict:
    pages = load_pages(export_dir)
    inlinks = load_links(export_dir, "all_inlinks.csv")
    text = load_page_text(export_dir)
    graph = build_graph(pages, inlinks)
    gstats = graph_stats(pages, inlinks, graph)
    anchors = anchor_analysis(inlinks)
    clusters = cluster_pages(pages, text)
    relate = relatedness(clusters["embeddings"], clusters["page_keywords"], top_per_page=50)
    cands = link_candidates(graph, relate, pages, clusters)
    return {
        "pages": pages, "graph": graph, "graph_stats": gstats,
        "anchors": anchors, "clusters": clusters, "relatedness": relate,
        "link_candidates": cands, "page_text_count": len(text),
    }

if __name__ == "__main__":
    import sys, json
    d = sys.argv[1] if len(sys.argv) > 1 else "../sample-export"
    res = analyze(d)
    g = res["graph_stats"]
    print(f"pages={g['pages_total']} indexable={g['pages_indexable']} "
          f"links={g['internal_links']} maxdepth={g['max_crawl_depth']}")
    print(f"orphans={len(g['orphan_pages'])} under_linked={len(g['under_linked_pages'])} "
          f"over_linked={len(g['over_linked_pages'])}")
    print(f"broken_internal={len(g['broken_internal_links'])} "
          f"redirect_internal={len(g['redirect_internal_links'])} "
          f"nofollow_internal={len(g['nofollow_internal_links'])}")
    a = res["anchors"]
    print(f"generic_anchors={len(a['generic_anchors'])} empty={len(a['empty_or_image_only'])} "
          f"over_optimized={len(a['over_optimized_anchors'])}")
    print(f"clusters={len(res['clusters']['clusters'])} "
          f"link_candidate_pages={len(res['link_candidates'])} "
          f"page_text={res['page_text_count']}")
