"""HTML report exporter with XSS protection and standalone responsive styling."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any


def _safe_str(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return html.escape(val.isoformat())
    return html.escape(str(val))


def export_html(investigation: dict[str, Any]) -> str:
    """Generate a secure, self-contained HTML report of an investigation."""
    inv_id = _safe_str(investigation.get("id"))
    status = _safe_str(investigation.get("status"))
    created_at = _safe_str(investigation.get("created_at"))
    completed_at = _safe_str(investigation.get("completed_at", "In progress"))
    request_data = investigation.get("request", {})
    findings = investigation.get("findings", [])
    entities = investigation.get("entities", [])
    edges = investigation.get("edges", [])
    warnings = investigation.get("warnings", [])
    summary = investigation.get("summary", {})

    status_badge_colors = {
        "found": "#16a34a",
        "not_found": "#64748b",
        "unknown": "#f59e0b",
        "info": "#0284c7",
        "error": "#dc2626",
    }

    findings_rows = []
    for f in findings:
        f_status = str(f.get("status", "unknown"))
        color = status_badge_colors.get(f_status, "#64748b")
        source_url = f.get("source_url")
        url_link = (
            f'<a href="{html.escape(str(source_url), quote=True)}" target="_blank" rel="noopener noreferrer">Source link</a>'
            if source_url
            else "None"
        )

        data_payload = f.get("data", {})
        data_preview = ""
        if data_payload:
            json_str = html.escape(json.dumps(data_payload, indent=2))
            data_preview = (
                f"<details><summary>Evidence Data</summary><pre>{json_str}</pre></details>"
            )

        findings_rows.append(f"""
        <tr>
            <td><span class="badge" style="background-color: {color};">{html.escape(f_status.upper())}</span></td>
            <td><strong>{_safe_str(f.get("title"))}</strong><br><small class="muted">{_safe_str(f.get("module_id"))} v{_safe_str(f.get("module_version"))}</small></td>
            <td>{_safe_str(f.get("evidence"))}{data_preview}</td>
            <td>{_safe_str(f.get("source_name"))}<br><small>{url_link}</small></td>
            <td>{_safe_str(f.get("confidence"))}</td>
            <td><small>{_safe_str(f.get("observed_at"))}</small></td>
        </tr>
        """)

    warnings_html = ""
    if warnings:
        items = "".join(f"<li>{_safe_str(w)}</li>" for w in warnings)
        warnings_html = (
            f'<div class="box warning-box"><h3>Warnings & Limitations</h3><ul>{items}</ul></div>'
        )

    entities_rows = []
    for e in entities:
        entities_rows.append(f"""
        <tr>
            <td><code>{_safe_str(e.get("id"))}</code></td>
            <td><span class="badge badge-gray">{_safe_str(e.get("type"))}</span></td>
            <td>{_safe_str(e.get("value"))}</td>
            <td>{_safe_str(e.get("display_label"))}</td>
        </tr>
        """)

    edges_rows = []
    for edge in edges:
        edges_rows.append(f"""
        <tr>
            <td><code>{_safe_str(edge.get("source_entity_id"))}</code></td>
            <td><strong>{_safe_str(edge.get("relation"))}</strong> ({_safe_str(edge.get("label"))})</td>
            <td><code>{_safe_str(edge.get("dest_entity_id"))}</code></td>
            <td>{_safe_str(edge.get("basis"))}</td>
            <td>{_safe_str(edge.get("confidence"))}</td>
        </tr>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenTrace Report - {inv_id}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --border: #334155;
            --text: #f8fafc;
            --muted: #94a3b8;
            --accent: #38bdf8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{ font-size: 1.75rem; font-weight: 700; color: var(--accent); }}
        h2 {{ font-size: 1.25rem; margin: 1.5rem 0 1rem; color: #e2e8f0; }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.2rem;
        }}
        .card strong {{ display: block; font-size: 0.8rem; text-transform: uppercase; color: var(--muted); }}
        .card span {{ font-size: 1.1rem; font-weight: 600; }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            color: #fff;
        }}
        .badge-gray {{ background: #475569; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--surface);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }}
        th {{ background: #1a2234; color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .muted {{ color: var(--muted); }}
        details {{ margin-top: 0.5rem; }}
        summary {{ cursor: pointer; color: var(--accent); font-size: 0.8rem; }}
        pre {{
            background: #090d16;
            padding: 0.5rem;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.8rem;
            margin-top: 0.5rem;
            border: 1px solid var(--border);
        }}
        .box {{
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }}
        .warning-box {{
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid #f59e0b;
            color: #fde68a;
        }}
        .warning-box ul {{ margin-left: 1.5rem; margin-top: 0.5rem; }}
        footer {{
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
            margin-top: 3rem;
            font-size: 0.8rem;
            color: var(--muted);
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>OpenTrace OSINT Report</h1>
                <p class="muted">Evidence-first digital footprint investigation</p>
            </div>
            <div>
                <span class="badge" style="font-size: 0.9rem; padding: 0.4rem 0.8rem; background-color: {"#16a34a" if status == "completed" else "#f59e0b"};">
                    Status: {status.upper()}
                </span>
            </div>
        </header>

        <div class="meta-grid">
            <div class="card">
                <strong>Investigation ID</strong>
                <span><code>{inv_id}</code></span>
            </div>
            <div class="card">
                <strong>Created (UTC)</strong>
                <span>{created_at}</span>
            </div>
            <div class="card">
                <strong>Completed (UTC)</strong>
                <span>{completed_at}</span>
            </div>
            <div class="card">
                <strong>Total Findings</strong>
                <span>{_safe_str(summary.get("total", len(findings)))}</span>
            </div>
            <div class="card">
                <strong>Targets</strong>
                <span>{_safe_str(", ".join(f"{k}: {v}" for k, v in request_data.items() if v and k != "modules")) or "None"}</span>
            </div>
        </div>

        {warnings_html}

        <h2>Findings ({len(findings)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Module / Title</th>
                    <th>Evidence</th>
                    <th>Source</th>
                    <th>Confidence</th>
                    <th>Observed</th>
                </tr>
            </thead>
            <tbody>
                {"".join(findings_rows) if findings_rows else '<tr><td colspan="6" class="muted">No findings recorded.</td></tr>'}
            </tbody>
        </table>

        <h2>Extracted Entities ({len(entities)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Entity ID</th>
                    <th>Type</th>
                    <th>Value</th>
                    <th>Display Label</th>
                </tr>
            </thead>
            <tbody>
                {"".join(entities_rows) if entities_rows else '<tr><td colspan="4" class="muted">No entities extracted.</td></tr>'}
            </tbody>
        </table>

        <h2>Evidence-Backed Edges ({len(edges)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Source ID</th>
                    <th>Relationship</th>
                    <th>Target ID</th>
                    <th>Basis</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
                {"".join(edges_rows) if edges_rows else '<tr><td colspan="5" class="muted">No relationships identified.</td></tr>'}
            </tbody>
        </table>

        <footer>
            <p>Generated by OpenTrace OSINT v0.1.0 · Public & Authorized Sources Only</p>
            <p>Disclaimer: Findings and candidate links denote technical observations, not confirmed identity proof.</p>
        </footer>
    </div>
</body>
</html>"""
