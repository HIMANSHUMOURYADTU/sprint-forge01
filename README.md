# Link Intel Suite - Forge 1 (Edition 2) starter

A Claude Code **plugin** that ingests a **Screaming Frog export** and produces an
**internal-linking + topical-authority** analysis: the internal link graph, anchor-text
issues, topical clusters, an entity graph, and the headline feature -
**contextual internal-link recommendations**. It serves a **live dashboard** plus an
exportable client report. The plumbing works out of the box - you implement the analysis
logic and push accuracy on the hidden export.

## Quick start (headless, proves it runs)
```bash
pip install mcp          # exposes MCP tools to Claude Code (dashboard works without it too)
python run.py sample-export/
# open the live cockpit:
#   http://localhost:7700
# outputs land in outputs/report.json and outputs/report.html
```

## Inside Claude Code
```
/link-intel sample-export/
```

## What's here
```
link-intel-suite/
|- .claude-plugin/plugin.json   plugin manifest (skill + command + 5 agents + MCP)
|- .claude/                     audit hooks (settings.json + hooks/audit.sh) - records process
|- skills/link-intel/SKILL.md   orchestrator
|- agents/                      graph-agent, anchor-agent, topic-agent, linker-agent, reporter
|- commands/link-intel.md       the /link-intel command
|- mcp/server.py                local MCP server + live dashboard host (localhost:7700)
|- linkintel/analyzer.py        deterministic analysis  <- EXTEND THIS to the full rulebook
|- dashboard/                   index.html + app.js (the cockpit)
|- scripts/export-transcript.sh saves your session transcript to agent-log.md (if available)
|- run.py                       headless runner (the grader's entry point)
|- rulebook.md                  exact analysis definitions
|- report.schema.json           the report.json output contract
`- outputs/                     report.json + report.html (generated)
```

## The sample export (`../sample-export/`)
A real Screaming Frog crawl of nmgtechnologies.com:
- `internal_html.csv` (also copied as `internal_all.csv`) - 1 row per page, all columns.
- `all_inlinks.csv` - every internal link (Type, Source, Destination, Anchor, Status Code,
  Follow, Link Position, Link Path, ...).
- `all_outlinks.csv`, `all_anchor_text.csv` - outbound links and anchor text.
- `page text/` - full body text per page (URL-encoded filenames).

## Your job
1. **Complete `linkintel/analyzer.py`** to the full `rulebook.md`: finish the anchor classes,
   improve clustering, sharpen the entity graph. Accuracy on the hidden export is the biggest
   part of your score.
2. **Wire the model steps** through the agents: name clusters (topic-agent), extract entities
   per page (topic-agent), and write the contextual link anchors (linker-agent).
3. **Improve the dashboard / report** to be genuinely client-ready.
4. **Commit incrementally** (>= 10 commits).

## The model - pick any from the allowed list (all free)
Run on the free local stack (Claude Code + Ollama). Set `OLLAMA_CONTEXT_LENGTH=65536` and use
a **tool-trained** model. Both local and Ollama free **cloud** models are allowed:

**Ollama free cloud** (good if your laptop has 8 GB RAM - these run on Ollama's servers):
- `gpt-oss:20b-cloud`
- `gemma3:27b-cloud`
- `qwen3-coder:480b-cloud`
- `deepseek-v3.1:671b-cloud`

**Local** (16 GB+ RAM, fully offline, unlimited):
- `qwen3:8b` / `qwen3:14b`
- `gemma3:12b`

Do not use `qwen2.5-coder` (a completion model - it prints raw tool JSON instead of running
tools). Set `RADAR_MODEL` / `LI_MODEL` to record which model you used in `report.json`.

## Model fairness - read this (it protects everyone equally)
Some people build on **8 GB-RAM laptops with Ollama free cloud models**. Those cloud models
**do not store local prompt history**, so `.claude/audit.jsonl` may be empty. **That is fine
and expected. The audit log is NOT mandatory and not having it does not cost you points.**

What is judged - and what guarantees your process is recorded regardless of model choice:
1. **The working plugin + a reproducible `report.json`** (run it on a fresh export, get the
   same answer). This is the primary basis: accuracy + working code + the repo.
2. **Incremental git commits** with real messages (the human-readable spine of your process).
3. **`PROMPTS.md`** - paste your key prompts here **manually** as you build.
4. **`DECISIONS.md`** - a short running log of real decisions and fixes.

The result (accuracy + working code + the repo) is the primary basis. Process is judged from
**git history + the manually-kept PROMPTS.md / DECISIONS.md**, NOT from an auto audit log.
If your model DOES write `audit.jsonl` (local sessions), commit it too - it only helps. If it
does not, you lose nothing. The hooks ship enabled as a convenience; leaving them on is fine
on every model.

## Submission
Submit your public GitHub repo link on the **build page** (not a third-party platform). See
the build brief for the full checklist and deadline.

## Note
The dashboard renders the operator's own crawl data on localhost; it is a local cockpit, not a
hardened public server. The shareable artifact is the exported `report.html`.
