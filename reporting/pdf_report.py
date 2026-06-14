import os
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(data, output_path):
    """
    Generates a professional PDF report from the analysis object.

    Args:
        data (dict): The report data (matching report.schema.json)
        output_path (str): Absolute path to save the PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=LETTER)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=24, fontSize=24)
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], alignment=1, spaceAfter=12, fontSize=14, textColor=colors.grey)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], spaceBefore=18, spaceAfter=10, fontSize=16)
    body_style = styles['BodyText']

    elements = []

    # 1. Cover Page
    elements.append(Spacer(1, 100))
    elements.append(Paragraph("Internal Linking Intelligence Report", title_style))
    elements.append(Paragraph(f"Site: {data['site']}", subtitle_style))
    elements.append(Paragraph(f"Pages Crawled: {data['pages_crawled']}", subtitle_style))
    elements.append(Paragraph(f"Generated on: {data['run_meta'].get('duration_sec', 'N/A')}s run", subtitle_style))
    elements.append(PageBreak())

    # 2. Executive Summary
    elements.append(Paragraph("Executive Summary", header_style))
    s = data['summary']
    summary_text = (
        f"The analysis of <b>{data['site']}</b> revealed a total of <b>{s['pages_crawled']}</b> pages. "
        f"The site contains <b>{s['internal_links']}</b> internal links, with <b>{s['orphan_pages']}</b> pages "
        f"identified as orphans and <b>{s['broken_internal_links']}</b> broken internal links. "
        f"We identified <b>{s['topical_clusters']}</b> distinct topical clusters and generated <b>{s['link_recommendations']}</b> "
        f"strategic internal linking recommendations to improve semantic authority."
    )
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 12))

    # 3. Site Metrics
    elements.append(Paragraph("Site Metrics", header_style))
    metrics_data = [
        ["Metric", "Value"],
        ["Total Pages Crawled", s['pages_crawled']],
        ["Indexable Pages", s['indexable_pages']],
        ["Total Internal Links", s['internal_links']],
        ["Orphan Pages", s['orphan_pages']],
        ["Broken Internal Links", s['broken_internal_links']],
        ["Generic Anchors", s['generic_anchors']],
        ["Topical Clusters", s['topical_clusters']],
        ["Link Recommendations", s['link_recommendations']],
    ]
    t_metrics = Table(metrics_data, colWidths=[250, 100])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (0, -1), colors.whitesmoke),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_metrics)

    # 4. Graph Analysis
    elements.append(Paragraph("Graph Analysis", header_style))
    g = data['link_graph']
    graph_text = (
        f"The link graph shows a maximum crawl depth of <b>{g['max_crawl_depth']}</b> "
        f"with an average of <b>{g['avg_inlinks']:.2f}</b> inlinks per page. "
    )
    elements.append(Paragraph(graph_text, body_style))

    graph_data = [
        ["Analysis Point", "Count"],
        ["Orphan Pages", len(g['orphan_pages'])],
        ["Deepest Pages", len(g['deepest_pages'])],
        ["Under-linked Pages", len(g['under_linked_pages'])],
        ["Over-linked Pages", len(g['over_linked_pages'])],
    ]
    t_graph = Table(graph_data, colWidths=[250, 100])
    t_graph.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_graph)

    # 5. Anchor Analysis
    elements.append(Paragraph("Anchor Analysis", header_style))
    a = data['anchor_text']
    anchor_text = (
        f"Total internal anchors analyzed: <b>{a['total_internal_anchors']}</b>. "
        f"We found <b>{len(a['generic_anchors'])}</b> generic anchors and "
        f"<b>{len(a['over_optimized_anchors'])}</b> over-optimized anchors that may impact SEO."
    )
    elements.append(Paragraph(anchor_text, body_style))

    anchor_data = [
        ["Anchor Category", "Count"],
        ["Generic / Non-descriptive", len(a['generic_anchors'])],
        ["Empty / Image Only", len(a['empty_or_image_only'])],
        ["Over-optimized Exact Match", len(a['over_optimized_anchors'])],
    ]
    t_anchor = Table(anchor_data, colWidths=[250, 100])
    t_anchor.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_anchor)

    # 6. Topical Clusters
    elements.append(Paragraph("Topical Clusters", header_style))
    cluster_data = [["Cluster Name", "Size", "Authority"]]
    for c in data['topical_clusters'][:20]:
        cluster_data.append([c['name'] or c['key'], c['size'], c['authority']])

    t_cluster = Table(cluster_data, colWidths=[300, 80, 100])
    t_cluster.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_cluster)

    # 7. Internal Link Recommendations
    elements.append(Paragraph("Internal Link Recommendations", header_style))
    rec_data = [["Source Page", "Target Page", "Suggested Anchor"]]
    for r in data['link_recommendations'][:25]:
        src = r['source'].replace("https://", "").replace("www.", "")
        tgt = r['target'].replace("https://", "").replace("www.", "")
        anchor = r.get('suggested_anchor') or "N/A"
        rec_data.append([src, tgt, anchor])

    t_rec = Table(rec_data, colWidths=[200, 200, 200])
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_rec)

    # 8. Conclusion
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Conclusion", header_style))

    conclusion_text = (
        f"The site <b>{data['site']}</b> shows a topical authority of " +
        ("Strong" if len(data['topical_clusters']) > 0 else "Undefined") +
        ". To improve overall semantic flow and search visibility, the site should prioritize: "
        f"<ul><li>Resolving <b>{s['orphan_pages']}</b> orphan pages.</li>"
        f"<li>Replacing <b>{s['generic_anchors']}</b> generic anchors with descriptive, keyword-rich text.</li>"
        f"<li>Implementing the {s['link_recommendations']} contextual recommendations to strengthen cluster hubs.</li></ul>"
    )
    elements.append(Paragraph(conclusion_text, body_style))

    doc.build(elements)
