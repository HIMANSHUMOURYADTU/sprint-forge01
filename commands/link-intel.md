---
description: Analyze a Screaming Frog export - build the internal link graph, audit anchors, cluster topics, build the entity graph, and produce contextual internal-link recommendations with a live dashboard + client report.
argument-hint: <export-folder>   e.g. /link-intel sample-export/
---

# /link-intel

Run a full internal-linking + topical-authority analysis on the Screaming Frog export folder
the user names in `$ARGUMENTS` (it should contain `internal_html.csv`, `all_inlinks.csv`, and
a `page text/` folder).

Invoke the **link-intel-suite skill** to run the pipeline: graph -> anchors -> topics +
entities -> contextual link recommendations -> report.

Tell the user to open **http://localhost:7700** to watch the live cockpit, and that the final
shareable deliverable is **outputs/report.html**.

Example:
`/link-intel sample-export/`

If the MCP server is not running, it should start with the plugin; otherwise start it with
`python mcp/server.py`.
