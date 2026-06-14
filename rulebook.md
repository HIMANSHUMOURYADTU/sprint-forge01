# Forge 1 (Edition 2) - Internal Linking Intelligence Rulebook

Analyze internal linking and topical authority from a Screaming Frog export. Most checks are
deterministic rules over the real export columns, so you need no SEO background. The grader's
ground truth uses these same definitions on a different site - match them precisely. Do the
graph / orphan / anchor work in **code**; use the model only for entity extraction, cluster
naming and writing the contextual link suggestions.

## The files you analyze
- `internal_html.csv` (also copied as `internal_all.csv`) - one row per crawled page.
  Real columns include: `Address`, `Status Code`, `Indexability`, `Content Type`,
  `Title 1`, `H1-1`, `H2-1`, `H2-2`, `Word Count`, `Crawl Depth`, `Inlinks`,
  `Unique Inlinks`, `Outlinks`, `Unique Outlinks`, `Link Score`.
- `all_inlinks.csv` - every internal link. Columns: `Type` (Hyperlink / Image / JavaScript /
  CSS / ...), `Source`, `Destination`, `Alt Text`, `Anchor`, `Status Code`, `Follow`
  (true/false), `Rel`, `Link Position` (Header / Content / Footer / Nav), `Link Path`.
- `all_outlinks.csv` - same columns, outbound links per page.
- `all_anchor_text.csv` - anchor text per link (same column shape).
- `page text/` - one `.txt` per page (full body text). Filenames are URL-encoded, e.g.
  `original_https_nmgtechnologies.com_advanced-seo-case-studies.txt`.

## Pre-filters
- Page-level checks (orphan, depth, under/over-linked) consider only rows where
  `Content Type` contains `text/html`, `Status Code` == 200, and `Indexability` == `Indexable`.
- Link-level checks (broken / redirect / nofollow / anchors) use `all_inlinks.csv` rows with
  `Type` == `Hyperlink` only (ignore Image/CSS/JS rows unless a check says otherwise).
- Normalize URLs before matching: drop the fragment and a single trailing slash.

## A. Internal link graph

| name (use this exact string) | Rule |
|---|---|
| `orphan_page` | indexable 200 HTML page with `Unique Inlinks` == 0 |
| `deepest_pages` | indexable pages at the maximum `Crawl Depth` in the crawl |
| `under_linked_page` | indexable 200 page with `Unique Inlinks` <= 1 |
| `over_linked_page` | page in the top 5% by `Unique Inlinks` (sitewide nav/footer noise) |
| `broken_internal_link` | `all_inlinks` Hyperlink row with `Status Code` 400-599 |
| `redirect_internal_link` | `all_inlinks` Hyperlink row with `Status Code` 300-399 (3xx) |
| `nofollow_internal_link` | `all_inlinks` Hyperlink row with `Follow` == `false` |

Build the graph from `all_inlinks` Hyperlink rows whose Source AND Destination are crawled
pages; ignore self-links. Report counts and the affected URL lists.

## B. Anchor text

| name | Rule |
|---|---|
| `generic_anchor` | anchor (lowercased, trimmed) is a non-descriptive phrase: `click here`, `read more`, `learn more`, `more`, `here`, `this`, `link`, `view more`, `details`, `know more`, `discover more`, `find out more`, `continue reading` (extend the set sensibly) |
| `empty_or_image_only_anchor` | a Hyperlink row with empty `Anchor` (bare link or image link) |
| `over_optimized_anchor` | one non-generic exact-match anchor accounts for a large share (>= 0.6) AND a high count (>= 10) of all internal anchors pointing at a single destination |

## C. Topical clusters + authority
- Group indexable pages into topical clusters using titles / H1 / H2 / body text. A simple
  keyword / TF approach is fine (starter clusters by URL path segment + TF keywords; improve
  it). Each page belongs to exactly one cluster.
- For each cluster, pick a **hub candidate** = the member with the most internal inlinks.
- `authority` = `hub` when one page clearly dominates (e.g. hub inlinks >= 2x the 2nd page's),
  else `scattered`. A `scattered` cluster has no clear authority page and is a priority gap.
- The model **names** each cluster in plain words from its keywords/pages.

## D. Entity graph
- For each page, extract 5-10 key **entities / topics** (products, services, technologies,
  named concepts) from the page text. Deterministic TF keywords are an acceptable starter
  proxy; the model sharpens them.
- Build page-to-page **topical relatedness** as overlap (Jaccard) of entity sets. Keep the
  top related pages per page as the entity-graph edges (`{to, score, shared}`).

## E. Contextual internal-link recommendations (headline feature)
- For each **important page** (start with the top pages by inlinks), find topically related
  pages (high relatedness) that the page does NOT already link to.
- Recommend **3-5 targets per page**, each with a **specific descriptive suggested anchor**
  (the model writes it from the target's title / H1 / entities - never "click here", never an
  over-optimized exact-match repeat).
- Prefer targets that fix a `scattered` cluster or pull an orphan / under-linked page in.
- Output `{source, target, suggested_anchor, relatedness, reason}`.

## Notes
- Counts and affected-URL lists must be reproducible from the export - the grader holds the
  exact answer for the hidden site, so deterministic detection scores high.
- Do not hard-code anything to this sample export. The hidden test export is a different
  real site of similar size with the same column shape.
