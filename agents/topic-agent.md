---
name: topic-agent
description: Builds topical clusters and the entity graph - computes clusters via the MCP topics tool, names each cluster with the model, extracts key entities per page from the page text, and feeds them back via the entities tool.
---

# Topic sub-agent

Group the site into topics, judge topical authority, and build the entity graph. This mixes
deterministic computation (clustering, relatedness math) with model judgment (naming,
entities).

## Clusters + authority
1. Call MCP `topics()`. It computes clusters (starter: by URL path segment + keyword TF) and,
   per cluster, a **hub candidate** (the member with the most internal inlinks) and an
   **authority** signal: `hub` if one page clearly dominates the cluster's inlinks,
   `scattered` otherwise.
2. For each cluster, read its keywords and a few member pages, then **name** it in plain
   words (e.g. "Ecommerce development services", "Case studies"). Call
   `topics({cluster_key: "Name", ...})` to attach the names.
3. Flag clusters that are `scattered` (no clear hub) - those are topical-authority gaps the
   recommendations should fix.

## Entity graph
4. For each important page, read its page text (from the `page text/` folder, already loaded)
   and extract **5-10 key entities / topics** (products, services, technologies, named
   concepts). One small model call per page; never dump the whole crawl into context.
5. Call MCP `entities({url: [entity, ...], ...})`. The server rebuilds the page-to-page
   relatedness graph on your entities and refreshes the link candidates.

Keep clustering + relatedness in code; use the model only to name clusters and pull entities.
