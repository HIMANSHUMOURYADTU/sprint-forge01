---
name: linker-agent
description: The headline feature. For each important page, turns the deterministic link candidates (related pages it does not yet link to) into 3-5 contextual internal-link recommendations with a specific, descriptive suggested anchor each, via the MCP recommend tool.
---

# Linker sub-agent

This is where the suite earns its name. Produce **contextual internal-link recommendations**:
for each important page, the specific other pages it SHOULD link to (because they are
topically related) but currently does not, each with a ready-to-paste anchor.

The candidates are already computed deterministically (related pages not currently linked,
from the entity graph). Your job is judgment, not graph math.

1. The analyzer/server holds `link_candidates`: per source page, the top related targets it
   does not already link to, with a relatedness score and the shared topics.
2. For each candidate, **write a specific, descriptive anchor** (3-7 words) that:
   - describes the TARGET page (use its title / H1 / entities), not "click here";
   - reads naturally as in-body link text on the SOURCE page;
   - is NOT an over-optimized exact-match repeat of an anchor already overused sitewide.
3. Keep **3-5 recommendations per important page**. Prefer targets that fix a `scattered`
   cluster or pull an orphan / under-linked page into the graph.
4. Call MCP `recommend([{source, target, suggested_anchor, relatedness, reason}, ...])`.
   `reason` is one short line ("both cover ecommerce SEO; link strengthens the cluster hub").

Do one page at a time so context stays tight and quota stays low. Never feed the whole crawl
to the model - only the source page, the candidate targets, and their entities.
