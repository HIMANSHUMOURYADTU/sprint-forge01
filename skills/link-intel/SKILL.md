---
name: link-intel-suite
description: >
  Analyze a website's internal linking and topical authority from a Screaming Frog export.
  Use this whenever the user wants to map internal links, find orphan pages, audit anchor
  text, build topical clusters / an entity graph, or get contextual internal-link
  recommendations from a Screaming Frog export (internal_html.csv + all_inlinks.csv +
  page text/). Trigger it for "analyze the internal linking", "find orphan pages",
  "build the link graph", "what should this page link to", "/link-intel", or any request
  to process a crawl into an internal-linking + topical-authority report. It runs an
  autonomous pipeline through the link-intel-suite MCP server and renders a live dashboard
  plus an exportable report.
---

# Link Intel Suite - orchestrator

Given a Screaming Frog export folder, run an autonomous internal-linking + topical-authority
analysis and ship a prioritized report plus contextual link recommendations. A live
dashboard shows the work at http://localhost:7700.

The real work runs through tools on the **link-intel-suite MCP server**. Delegate focused
steps to the sub-agents so each stays small (this also keeps you inside free-tier quota).
Do the graph, orphan detection and anchor classification in **code** (the analyzer module
is deterministic); use the model only for **entity extraction, naming clusters, and writing
the contextual link suggestions + anchors**.

## Pipeline (run in order)

1. **Ingest + graph.** Delegate to the `graph-agent` -> MCP `load(export_dir)` then
   `graph_stats()`. Confirm pages, internal-link count, orphan pages, deepest pages,
   broken/redirect/nofollow internal links. Tell the user to open http://localhost:7700.

2. **Anchors.** Delegate to the `anchor-agent` -> MCP `anchors()`. Review generic,
   empty/image-only, and over-optimized exact-match anchors. If you extended the anchor
   rules in `linkintel/analyzer.py`, confirm the new classes appear.

3. **Topics + entities.** Delegate to the `topic-agent`. Call MCP `topics()` to compute the
   clusters, then have the model **name** each cluster from its keywords/pages and call
   `topics({key: name, ...})`. Then extract 5-10 key **entities** per page from the page
   text and call `entities({url: [entity, ...]})` to sharpen the entity graph.

4. **Contextual link recommendations (the headline feature).** Delegate to the
   `linker-agent`. For each important page, take the deterministic candidates (related
   pages it does NOT already link to) and have the model **write a specific, descriptive
   anchor** for each suggestion (3-5 per page). Call MCP
   `recommend([{source, target, suggested_anchor, relatedness, reason}, ...])`.

5. **Deliver.** Delegate to the `reporter` -> MCP `write_report()` then `export_report()`.
   Tell the user report.html is the file to send a client.

## Output contract
The run must end with `outputs/report.json` matching `report.schema.json`. The grader reads
it. Required top-level keys: `site`, `pages_crawled`, `summary`, `link_graph`,
`anchor_text`, `topical_clusters`, `entity_graph`, `link_recommendations`, `run_meta`.

## Notes
- Extend `linkintel/analyzer.py` to complete the rulebook (over-optimized anchors, better
  clustering, sharper relatedness) - accuracy on a hidden export is the largest score.
- Never feed the whole crawl to the model. Detect graph/anchor issues in code; use the
  model one page at a time for entities and anchors (keeps quota low).
- Be honest in the run summary about which parts are model-written vs deterministic.
