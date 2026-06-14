
from __future__ import annotations

import os
from reporting.pdf_report import generate_pdf_report
from reporting.ppt_report import generate_ppt_report
import argparse, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "mcp"))
sys.path.insert(0, HERE)
import server  # the MCP server module exposes every tool as a function


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("--no-dashboard", action="store_true")
    args = ap.parse_args()

    if not args.no_dashboard:
        server.start_dashboard()
        print(f"[li] dashboard: http://localhost:{server.PORT}", flush=True)
        time.sleep(1)

    t0 = time.time()
    server.li_load(args.export_dir)
    server.li_graph()
    server.li_anchors()
    server.li_topics()        # no model names in headless mode (cluster keys used)
    server.li_entities()      # uses TF-keyword relatedness proxy
    # Starter does NOT attach model-written recs; _report_obj() then falls back to the
    # deterministic candidates (no anchors) so the contract always has data to grade.
    server.RUN["model_calls"] = 0
    server.RUN["duration_sec"] = round(time.time() - t0, 1)
    server.li_report()
    server.li_export()
    try:
        report_data = server.RUN

        generate_pdf_report(
            report_data,
            os.path.join(HERE, "outputs", "report.pdf")
        )

        generate_ppt_report(
            report_data,
            os.path.join(HERE, "outputs", "report.pptx")
        )

        print("Wrote outputs/report.pdf")
        print("Wrote outputs/report.pptx")

    except Exception as e:
        print(f"[WARN] Report generation failed: {e}")

    s = server.RUN["summary"]
    print("\n=== INTERNAL LINKING INTELLIGENCE ===")
    print(f"Site            : {server.RUN['site']}  ({s['pages_crawled']} pages)")
    print(f"Internal links  : {s['internal_links']}")
    print(f"Orphan pages    : {s['orphan_pages']}")
    print(f"Broken internal : {s['broken_internal_links']}")
    print(f"Generic anchors : {s['generic_anchors']}")
    print(f"Topical clusters: {s['topical_clusters']}")
    print(f"Link suggestions: {s['link_recommendations']}")
    print("Wrote outputs/report.json and outputs/report.html")


if __name__ == "__main__":
    main()
