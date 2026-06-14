// app.js - live cockpit for the Link Intel Suite. Subscribes to the MCP server's
// SSE stream (/events) and paints KPIs, the graph panel, clusters and recommendations
// as the analysis runs. Falls back to polling /state if SSE drops.

const $ = (id) => document.getElementById(id);
function set(id, v){ const el = $(id); if(el) el.textContent = (v === undefined || v === null) ? "-" : v; }

function paint(RUN){
  if(!RUN) return;
  if(RUN.site) set("site", RUN.site);
  if(RUN.status) set("status", RUN.status);
  const g = RUN.graph_stats, a = RUN.anchors, e = RUN.entities, s = RUN.summary;
  if(g){
    set("k-links", g.internal_links); set("k-orphans", g.orphan_pages);
    set("k-broken", g.broken_internal_links);
    set("g-pages", g.pages_total); set("g-idx", g.pages_indexable);
    set("g-depth", g.max_crawl_depth); set("g-avg", g.avg_inlinks);
    set("g-deep", g.deepest_pages); set("g-under", g.under_linked_pages);
    set("g-over", g.over_linked_pages); set("g-redir", g.redirect_internal_links);
    set("g-nofol", g.nofollow_internal_links);
  }
  if(a){
    set("k-generic", a.generic); set("a-total", a.total);
    set("a-generic", a.generic); set("a-empty", a.empty_or_image_only);
    set("a-over", a.over_optimized);
  }
  if(e){ set("e-pages", e.pages_with_entities); }
  if(RUN.clusters){
    set("k-clusters", RUN.clusters.length);
    const html = RUN.clusters.map(c =>
      `<div class="cl"><span><strong>${c.name || c.key}</strong> <span class="st">(${c.size} pages)</span></span>`+
      `<span class="tag ${c.authority}">${c.authority}</span></div>`).join("");
    $("clusters").innerHTML = html || '<div class="empty">No clusters yet.</div>';
  }
  if(RUN.recommendations !== undefined && RUN.recommendations !== null){
    set("k-recs", typeof RUN.recommendations === "number" ? RUN.recommendations : RUN.recommendations);
  }
  if(s) set("k-recs", s.link_recommendations);
}

function feed(line){
  const f = $("feed"); if(!f) return;
  const d = document.createElement("div");
  d.textContent = "[" + new Date().toLocaleTimeString() + "] " + line;
  f.prepend(d);
  while(f.childNodes.length > 60) f.removeChild(f.lastChild);
}

let RUN = {};
function onEvent(evt){
  const { event, data } = evt;
  if(event === "snapshot"){ RUN = data || {}; paint(RUN); feed("connected"); return; }
  if(event === "loaded"){ RUN.site = data.site; RUN.urls = data.urls; feed(`loaded ${data.urls} pages, ${data.page_text} page texts`); }
  if(event === "graph"){ RUN.graph_stats = data; feed(`graph: ${data.orphan_pages} orphans, ${data.broken_internal_links} broken`); }
  if(event === "anchors"){ RUN.anchors = data; feed(`anchors: ${data.generic} generic, ${data.empty_or_image_only} empty`); }
  if(event === "topics"){ RUN.clusters = data.clusters; feed(`topics: ${data.clusters.length} clusters`); }
  if(event === "entities"){ RUN.entities = data; feed(`entities on ${data.pages_with_entities} pages`); }
  if(event === "recommendations"){ RUN.recommendations = data.count; feed(`${data.count} link recommendations`); }
  if(event === "saved"){ RUN.status = "done"; feed("report.json written"); }
  if(event === "exported"){ feed("report.html exported"); }
  paint(RUN);
}

function connect(){
  try{
    const es = new EventSource("/events");
    es.onmessage = (m) => { try{ onEvent(JSON.parse(m.data)); }catch(e){} };
    es.onerror = () => { es.close(); setTimeout(poll, 1500); };
  }catch(e){ poll(); }
}
function poll(){
  fetch("/state").then(r=>r.json()).then(d=>{ RUN = d; paint(RUN); }).catch(()=>{});
  setTimeout(poll, 3000);
}
connect();
