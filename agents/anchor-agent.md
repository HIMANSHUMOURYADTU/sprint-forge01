---
name: anchor-agent
description: Classifies internal anchor text via the MCP anchors tool - generic / non-descriptive anchors, empty / image-only anchors, and over-optimized exact-match anchors.
---

# Anchor sub-agent

Audit how the site links to itself, by the words in the links.

1. Call MCP `anchors()`. It runs the deterministic anchor classifier in
   `linkintel/analyzer.py` and streams the result to the dashboard.
2. Review the three classes (definitions in `rulebook.md`):
   - **generic / non-descriptive** = anchor text in the generic set
     ("click here", "read more", "learn more", "here", ...). These waste link equity and
     tell search engines nothing about the target.
   - **empty / image-only** = a Hyperlink row with no anchor text (bare or image link).
   - **over-optimized exact-match** = the same keyword anchor pointing at one destination
     from many sources (keyword-stuffing / unnatural-pattern signal).
3. Confirm the counts and flag the worst offenders for the orchestrator and the linker-agent
   (generic anchors are prime rewrite candidates).

Detection stays in code. The model's later job (linker-agent) is to write better anchors -
not to classify the existing ones here.
