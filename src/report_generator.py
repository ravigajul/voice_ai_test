"""
HTML Test Report Generator for Papa John's Voice Ordering Tests.

Generates a self-contained HTML report after each end-to-end test run.
Screenshots are embedded as base64 data URIs when show_images=True.
"""

import base64
import os
from datetime import datetime
from pathlib import Path

# Screenshot filename stem → human-readable caption (in display order)
SCREENSHOT_CAPTIONS = [
    ("step1_app_launched",              "Step 1: App Launched"),
    ("step2_start_voice_order_visible", "Step 2: Voice Order Button Visible"),
    ("step3_voice_agent_launched",      "Step 3: Voice Agent Screen"),
    ("step4_after_arrow_click",         "Step 4: After Arrow Click"),
    ("step6_agent_verified",            "Step 6: Voice Agent Verified"),
    ("step6_agent_not_verified",        "Step 6: Agent Not Verified"),
    ("order_complete_screen",           "Order Complete"),
    ("order_complete_overview",         "Order Overview Tab"),
    ("order_complete_details",          "Order Details Tab"),
    ("cart_verification",               "Cart Screen"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _duration_str(start: datetime, end: datetime) -> str:
    delta = end - start
    total = int(delta.total_seconds())
    m, s = divmod(total, 60)
    return f"{m}m {s}s" if m else f"{s}s"


def _phase_icon(status: str) -> str:
    return {"passed": "✅", "failed": "❌", "skipped": "⏭"}.get(status, "❓")


def _phase_color(status: str) -> str:
    return {"passed": "#22c55e", "failed": "#ef4444", "skipped": "#94a3b8"}.get(status, "#94a3b8")


def _esc(text) -> str:
    """Minimal HTML escaping. Accepts any type and converts to string first."""
    text = text if isinstance(text, str) else str(text)
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


# ─────────────────────────────────────────────────────────────────────────────
# Conversation log parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_conversation(log_file: str) -> list[dict]:
    """
    Parse conversation log into a list of turn dicts.
    Returns: [{"speaker": "Agent"|"Ravi"|"system", "text": "..."}]
    """
    turns = []
    if not log_file or not os.path.isfile(log_file):
        return turns

    with open(log_file, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("Agent:"):
                text = line[len("Agent:"):].strip()
                if text:
                    turns.append({"speaker": "Agent", "text": text})
            elif line.startswith("Ravi:"):
                text = line[len("Ravi:"):].strip()
                if text:
                    turns.append({"speaker": "Ravi", "text": text})
            elif line.startswith("[") and line.endswith("]"):
                turns.append({"speaker": "system", "text": line})
    return turns


# ─────────────────────────────────────────────────────────────────────────────
# HTML section builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_styles() -> str:
    return """
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; }
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
             background: #f1f5f9; color: #1e293b; line-height: 1.5; }

      /* Header */
      .header { background: linear-gradient(135deg, #1e3a5f 0%, #c8102e 100%);
                color: white; padding: 28px 40px; display: flex;
                align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
      .header h1 { font-size: 1.6rem; font-weight: 700; }
      .header .meta { font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }

      /* Overall badge */
      .badge { display: inline-flex; align-items: center; gap: 8px;
               padding: 10px 22px; border-radius: 999px; font-weight: 700;
               font-size: 1.05rem; letter-spacing: 0.04em; }
      .badge.passed { background: #22c55e; color: white; }
      .badge.failed { background: #ef4444; color: white; }

      /* Sections */
      .section { background: white; border-radius: 12px; padding: 28px 32px;
                 margin: 24px 40px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
      .section h2 { font-size: 1.1rem; font-weight: 700; color: #1e3a5f;
                    border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;
                    margin-bottom: 20px; }

      /* Config table */
      .config-table { width: 100%; border-collapse: collapse; }
      .config-table td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-size: 0.92rem; }
      .config-table td:first-child { color: #64748b; width: 180px; font-weight: 600; }

      /* Phase cards */
      .phases { display: flex; gap: 16px; flex-wrap: wrap; }
      .phase-card { flex: 1; min-width: 200px; border-radius: 10px; padding: 18px 20px;
                    display: flex; align-items: center; gap: 14px; }
      .phase-card .icon { font-size: 1.8rem; line-height: 1; }
      .phase-card .info .label { font-weight: 700; font-size: 0.95rem; }
      .phase-card .info .status { font-size: 0.82rem; text-transform: uppercase;
                                   letter-spacing: 0.06em; font-weight: 600; margin-top: 2px; }

      /* Items table */
      .items-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
      .items-table th { background: #f8fafc; padding: 10px 14px; text-align: left;
                         color: #64748b; font-weight: 600; font-size: 0.8rem;
                         text-transform: uppercase; letter-spacing: 0.05em; }
      .items-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
      .items-table tr.matched td { background: #f0fdf4; }
      .items-table tr.missing td { background: #fef2f2; }
      .items-table tr.extra td { background: #fff7ed; }
      .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
                     margin-right: 8px; }
      .dot-green { background: #22c55e; }
      .dot-red   { background: #ef4444; }
      .dot-orange{ background: #f97316; }

      /* Overview mini-table */
      .overview-table { width: 100%; border-collapse: collapse; margin-top: 16px;
                         font-size: 0.9rem; }
      .overview-table td { padding: 7px 12px; border-bottom: 1px solid #f1f5f9; }
      .overview-table td:first-child { color: #64748b; font-weight: 600; width: 160px; }

      /* Score ring */
      .score-row { display: flex; align-items: center; gap: 24px; margin-bottom: 20px; }
      .score-circle { width: 80px; height: 80px; border-radius: 50%;
                       display: flex; align-items: center; justify-content: center;
                       font-size: 1.4rem; font-weight: 800; color: white;
                       flex-shrink: 0; }
      .score-desc { font-size: 0.9rem; color: #64748b; }
      .score-desc strong { color: #1e293b; font-size: 1rem; }

      /* Chat bubbles */
      .chat { display: flex; flex-direction: column; gap: 10px; }
      .bubble-wrap { display: flex; flex-direction: column; }
      .bubble-wrap.agent { align-items: flex-start; }
      .bubble-wrap.ravi  { align-items: flex-end; }
      .speaker-label { font-size: 0.72rem; font-weight: 700; color: #94a3b8;
                        text-transform: uppercase; letter-spacing: 0.06em;
                        margin-bottom: 3px; padding: 0 4px; }
      .bubble { max-width: 70%; padding: 10px 14px; border-radius: 16px;
                 font-size: 0.9rem; line-height: 1.5; }
      .bubble.agent { background: #f1f5f9; color: #1e293b; border-bottom-left-radius: 4px; }
      .bubble.ravi  { background: #1e3a5f; color: white; border-bottom-right-radius: 4px; }
      .bubble.system { background: #fef9c3; color: #92400e; font-style: italic;
                        border-radius: 8px; font-size: 0.82rem; max-width: 100%; }

      /* Screenshots */
      .screenshot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
                           gap: 20px; }
      .screenshot-card { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;
                           box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
      .screenshot-card img { width: 100%; display: block; object-fit: contain;
                               background: #0f172a; max-height: 420px; }
      .screenshot-caption { padding: 8px 12px; font-size: 0.8rem; color: #64748b;
                              font-weight: 600; background: #f8fafc; }

      /* Reasoning box */
      .reasoning { background: #f8fafc; border-left: 4px solid #94a3b8; border-radius: 6px;
                    padding: 12px 16px; font-size: 0.88rem; color: #475569; margin-top: 16px; }
    </style>
"""


def _build_header(metadata: dict, passed: bool, score: int) -> str:
    start: datetime = metadata.get("start_time", datetime.now())
    end: datetime = metadata.get("end_time", datetime.now())
    ts = start.strftime("%Y-%m-%d %H:%M:%S")
    dur = _duration_str(start, end)

    badge_class = "passed" if passed else "failed"
    badge_text = "PASSED" if passed else "FAILED"

    return f"""
    <div class="header">
      <div>
        <h1>Papa John's Voice Ordering Test Report</h1>
        <div class="meta">{_esc(ts)} &nbsp;|&nbsp; Duration: {_esc(dur)}</div>
      </div>
      <div style="display:flex;align-items:center;gap:16px;">
        <div class="badge {badge_class}">{badge_text}</div>
        <div class="badge" style="background:#1e3a5f;">Score: {score}/100</div>
      </div>
    </div>
"""


def _build_config(metadata: dict) -> str:
    persona    = _esc(metadata.get("persona") or "default")
    scenario   = _esc(metadata.get("scenario") or "—")
    mic        = _esc(metadata.get("mic") or "—")
    session_id = _esc(metadata.get("session_id") or "—")

    rows = [
        ("Persona",    persona),
        ("Scenario",   scenario),
        ("Microphone", mic),
        ("Session ID", session_id),
    ]
    rows_html = []
    for k, v in rows:
        if k == "Session ID" and v and v != "—":
            # Monospace + click-to-copy for easy sharing when debugging
            cell = (
                f'<code style="font-family:monospace;background:#f1f5f9;'
                f'padding:2px 6px;border-radius:4px;user-select:all;">{v}</code>'
                f' <span style="font-size:0.75rem;color:#94a3b8;">(click to select)</span>'
            )
        else:
            cell = v
        rows_html.append(f'<tr><td>{k}</td><td>{cell}</td></tr>')
    rows_html = "\n".join(rows_html)
    return f"""
    <div class="section">
      <h2>Test Configuration</h2>
      <table class="config-table">
        {rows_html}
      </table>
    </div>
"""


def _build_phases(phase_statuses: dict) -> str:
    phases = [
        ("navigation",    "Phase 1", "Navigation to Voice Agent"),
        ("conversation",  "Phase 2", "AI Customer Conversation"),
        ("verification",  "Phase 3", "Order Verification"),
    ]
    cards = []
    for key, num, label in phases:
        status = phase_statuses.get(key, "skipped")
        icon   = _phase_icon(status)
        color  = _phase_color(status)
        cards.append(f"""
        <div class="phase-card" style="background:{color}18;border:1px solid {color}40;">
          <div class="icon">{icon}</div>
          <div class="info">
            <div class="label">{_esc(num)}: {_esc(label)}</div>
            <div class="status" style="color:{color};">{_esc(status)}</div>
          </div>
        </div>""")

    return f"""
    <div class="section">
      <h2>Test Phases</h2>
      <div class="phases">{''.join(cards)}</div>
    </div>
"""


def _build_verification(results: dict) -> str:
    matched = results.get("matched_items", [])
    missing = results.get("missing_items", [])
    extra   = results.get("extra_items", [])
    score   = results.get("score", 0)
    passed  = results.get("passed", False)
    reasoning = results.get("reasoning", "")
    overview  = results.get("overview") or {}

    score_color = "#22c55e" if score >= 80 else "#f97316" if score >= 50 else "#ef4444"

    # Items table rows
    item_rows = []
    for item in matched:
        item_rows.append(
            f'<tr class="matched"><td><span class="status-dot dot-green"></span>Matched</td>'
            f'<td>{_esc(item)}</td></tr>'
        )
    for item in missing:
        item_rows.append(
            f'<tr class="missing"><td><span class="status-dot dot-red"></span>Missing</td>'
            f'<td>{_esc(item)}</td></tr>'
        )
    for item in extra:
        item_rows.append(
            f'<tr class="extra"><td><span class="status-dot dot-orange"></span>Extra</td>'
            f'<td>{_esc(item)}</td></tr>'
        )

    items_table = ""
    if item_rows:
        items_table = f"""
        <table class="items-table">
          <thead><tr><th>Status</th><th>Item</th></tr></thead>
          <tbody>{''.join(item_rows)}</tbody>
        </table>"""
    else:
        items_table = '<p style="color:#94a3b8;font-size:0.9rem;">No items to display.</p>'

    # Overview mini-table
    ov_fields = [
        ("Order #",     overview.get("order_number")),
        ("Item count",  overview.get("item_count")),
        ("Payment",     overview.get("payment")),
        ("Order total", overview.get("order_total")),
        ("Total amount",overview.get("order_total_amount")),
    ]
    ov_rows = "".join(
        f'<tr><td>{k}</td><td>{_esc(v)}</td></tr>'
        for k, v in ov_fields if v
    )
    overview_html = f"""
        <h3 style="margin:20px 0 8px;font-size:0.95rem;color:#1e3a5f;">Order Overview</h3>
        <table class="overview-table"><tbody>{ov_rows}</tbody></table>""" if ov_rows else ""

    reasoning_html = (
        f'<div class="reasoning"><strong>Reasoning:</strong> {_esc(reasoning)}</div>'
        if reasoning else ""
    )

    return f"""
    <div class="section">
      <h2>Order Verification</h2>
      <div class="score-row">
        <div class="score-circle" style="background:{score_color};">{score}</div>
        <div class="score-desc">
          <strong>{'Order verified successfully' if passed else 'Order verification failed'}</strong><br>
          Matched: {len(matched)} &nbsp;|&nbsp; Missing: {len(missing)} &nbsp;|&nbsp; Extra: {len(extra)}
        </div>
      </div>
      {items_table}
      {overview_html}
      {reasoning_html}
    </div>
"""


def _build_conversation(log_file: str) -> str:
    turns = _parse_conversation(log_file)
    if not turns:
        return ""

    bubbles = []
    for turn in turns:
        speaker = turn["speaker"]
        text    = _esc(turn["text"])
        if speaker == "system":
            bubbles.append(
                f'<div class="bubble-wrap agent">'
                f'<div class="bubble system">{text}</div></div>'
            )
        elif speaker == "Agent":
            bubbles.append(
                f'<div class="bubble-wrap agent">'
                f'<div class="speaker-label">Voice Agent</div>'
                f'<div class="bubble agent">{text}</div></div>'
            )
        else:
            bubbles.append(
                f'<div class="bubble-wrap ravi">'
                f'<div class="speaker-label">Ravi (AI Customer)</div>'
                f'<div class="bubble ravi">{text}</div></div>'
            )

    return f"""
    <div class="section">
      <h2>Conversation Transcript ({len(turns)} turns)</h2>
      <div class="chat">{''.join(bubbles)}</div>
    </div>
"""


def _build_screenshots(screenshot_dir: str) -> str:
    cards = []
    for stem, caption in SCREENSHOT_CAPTIONS:
        path = os.path.join(screenshot_dir, f"{stem}.png")
        if not os.path.isfile(path):
            continue
        try:
            b64 = _img_to_base64(path)
        except Exception:
            continue
        cards.append(f"""
        <div class="screenshot-card">
          <img src="data:image/png;base64,{b64}" alt="{_esc(caption)}">
          <div class="screenshot-caption">{_esc(caption)}</div>
        </div>""")

    if not cards:
        return ""

    return f"""
    <div class="section">
      <h2>Screenshots ({len(cards)})</h2>
      <div class="screenshot-grid">{''.join(cards)}</div>
    </div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_html_report(
    results: dict,
    log_file: str | None,
    show_images: bool,
    metadata: dict,
    phase_statuses: dict,
    screenshot_dir: str,
) -> str:
    """
    Generate a self-contained HTML test report.

    Args:
        results:        dict from verify_order() — passed, score, matched/missing/extra, overview
        log_file:       path to conversation log (logs/test_run_*.txt) or None
        show_images:    if True, embed screenshots as base64 in the report
        metadata:       dict with keys: persona, scenario, mic, start_time, end_time
        phase_statuses: dict with keys: navigation, conversation, verification
                        each value is "passed" | "failed" | "skipped"
        screenshot_dir: directory where Appium screenshots are saved

    Returns:
        Absolute path to the generated HTML file (inside reports/)
    """
    passed = results.get("passed", False)
    score  = results.get("score", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Voice Order Test Report - {metadata.get('start_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}</title>
  {_build_styles()}
</head>
<body>
  {_build_header(metadata, passed, score)}
  {_build_config(metadata)}
  {_build_phases(phase_statuses)}
  {_build_verification(results)}
  {_build_conversation(log_file or '')}
  {_build_screenshots(screenshot_dir) if show_images else ''}
  <div style="text-align:center;padding:24px 0 32px;color:#94a3b8;font-size:0.8rem;">
    Generated by pizza-voice-test &nbsp;|&nbsp;
    {metadata.get('end_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
  </div>
</body>
</html>"""

    # Save report
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    ts = metadata.get("end_time", datetime.now()).strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"report_{ts}.html"
    report_path.write_text(html, encoding="utf-8")

    return str(report_path.resolve())
