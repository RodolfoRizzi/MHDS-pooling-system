"""Stateless component helpers (cards, buttons, headers, captions)."""

from __future__ import annotations

import panel as pn

from .tokens import ACCENT, BORDER, FS_H2, FS_H3, FS_BODY, SURFACE, TEXT, TEXT_MUTED


# ── Style helpers ─────────────────────────────────────────────────────────
def card_styles(extra=None):
    s = {
        "background": SURFACE,
        "color": TEXT,
        "border": f"1px solid {BORDER}",
        "border-radius": "10px",
        "padding": "14px",
        "margin-bottom": "12px",
    }
    if extra:
        s.update(extra)
    return s


def btn_css(bg, fg, hover, border="none"):
    return [
        f"""
        :host .bk-btn, :host .bk-btn-group .bk-btn {{
            background:{bg} !important; color:{fg} !important;
            border:{border} !important; border-radius:8px !important;
            font-weight:600 !important;
        }}
        :host .bk-btn:hover {{ background:{hover} !important; }}
    """
    ]


def section_header(icon, text):
    return pn.pane.HTML(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin:4px 0 14px 0;">
          <div style="width:4px;height:22px;background:{ACCENT};border-radius:2px;"></div>
          <span style="font-size:{FS_H2};">{icon}</span>
          <span style="font-size:{FS_H2};font-weight:700;letter-spacing:.2px;color:{TEXT};">{text}</span>
        </div>
        """,
        sizing_mode="stretch_width",
        margin=0,
    )


def modal_header(title, description, desc_color=None):
    color = desc_color or TEXT_MUTED
    return pn.pane.HTML(
        f'<div style="margin-bottom:16px;">'
        f'<div style="font-size:{FS_H3};font-weight:700;color:{TEXT};margin-bottom:5px;">{title}</div>'
        f'<div style="font-size:{FS_BODY};color:{color};line-height:1.45;">{description}</div>'
        f"</div>",
        sizing_mode="stretch_width",
        margin=0,
    )


def description(text):
    """Caption-style intro text under a section header (e.g. above each
    Answers table). Single pn.pane.Markdown with explicit styles — kept as
    one pane (not a Column of two) so the wrapping figures_col doesn't
    collapse, which is what broke the earlier subsection_intro attempt."""
    return pn.pane.Markdown(
        text,
        styles={"font-size": FS_BODY, "color": TEXT, "line-height": "1.5"},
        sizing_mode="stretch_width",
    )
