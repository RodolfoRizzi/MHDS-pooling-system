"""Row → Panel object builders."""

from __future__ import annotations

import ast

import pandas as pd
import panel as pn

from ..config import (
    DASS_ITEMS,
    FACTOR_LABEL,
    FILTER_GROUPS,
    TOPIC_COLS,
    TOPIC_OPTIONS,
    TOPIC_QUESTIONS,
)
from .components import card_styles, description
from .tokens import FIRST_COL_BOLD_CSS, GROUP_COLORS, TABLE_CSS, TEXT


def render_persona_card(row):
    """Render the header card summarising one persona's traits."""
    if row is None:
        return ""

    def has(c):
        return c in row and pd.notna(row[c]) and str(row[c]).strip() not in ("nan", "")

    def li(c):
        return f'<li style="margin:3px 0;"><b>{c.replace("_", " ").title()}:</b> {row[c]}</li>'

    meta = "  ·  ".join(
        f"<b>{c.replace('_', ' ').title()}:</b> {row[c]}"
        for c in FILTER_GROUPS["LLMs / Modality"]
        if has(c)
    )
    columns = ""
    for group, color in GROUP_COLORS.items():
        items = "".join(li(c) for c in FILTER_GROUPS[group] if has(c))
        # Group title: bumped from .72rem to .88rem so the bold (700) actually
        # reads as bold — at the previous size the uppercase + colored text
        # looked thin despite the weight setting.
        columns += (
            '<div style="flex:1 1 200px;min-width:200px;">'
            f'<div style="font-size:.84rem;font-weight:800;text-transform:uppercase;'
            f"letter-spacing:.5px;color:{color};border-bottom:2px solid {color};"
            f'padding-bottom:4px;margin-bottom:8px;">{group}</div>'
            f'<ul style="margin:0;padding-left:18px;list-style:disc;color:{TEXT};">{items}</ul>'
            "</div>"
        )
    return (
        '<div style="display:flex;gap:14px;align-items:center;margin-bottom:12px;">'
        '<div style="font-size:2.4rem;line-height:1;">👤</div>'
        f'<div style="font-size:.95rem;color:{TEXT};">{meta}</div></div>'
        f'<div style="display:flex;gap:28px;flex-wrap:wrap;">{columns}</div>'
    )


def build_topics(row):
    rows = []
    for name in TOPIC_OPTIONS:
        tcol = TOPIC_COLS[name]
        text = str(row[tcol]) if tcol in row and pd.notna(row[tcol]) else "—"
        rows.append(
            {"Topic": name, "Question": TOPIC_QUESTIONS[name], "Response": text}
        )
    table = pn.widgets.Tabulator(
        pd.DataFrame(rows),
        sizing_mode="stretch_width",
        show_index=False,
        theme="default",
        pagination=None,
        layout="fit_columns",
        disabled=True,
        stylesheets=[TABLE_CSS, FIRST_COL_BOLD_CSS],
        configuration={
            "columnDefaults": {"headerWordWrap": True, "headerSort": False},
            "columns": [
                {"field": "Topic", "widthGrow": 1, "formatter": "textarea"},
                {"field": "Question", "widthGrow": 2, "formatter": "textarea"},
                {"field": "Response", "widthGrow": 4, "formatter": "textarea"},
            ],
        },
    )
    return pn.Column(
        description(
            "**Topic Responses** — Six open-ended mental-health questions (family "
            "support, medications, professional help, stigma, AI psychologists, OCD "
            "symptoms), each answered in a short first-person reply (~50–80 words) "
            "shaped by the persona's traits."
        ),
        table,
        sizing_mode="stretch_width",
        styles=card_styles(),
    )


def build_ert(row):
    ert_raw = row["ert"] if "ert" in row and pd.notna(row["ert"]) else None
    words = []
    if ert_raw:
        try:
            words = ast.literal_eval(ert_raw) if isinstance(ert_raw, str) else ert_raw
        except Exception:
            words = [str(ert_raw)]

    prompt = description(
        "**Emotional Recall Task (ERT)** — A free-recall task: the persona lists ten "
        "English words describing feelings experienced over the past month, capturing "
        "spontaneous affective language to complement the structured DASS-21."
    )
    if not words:
        return pn.Column(
            prompt,
            pn.pane.Markdown("_No ERT data available._"),
            sizing_mode="stretch_width",
            styles=card_styles(),
        )
    table = pn.widgets.Tabulator(
        pd.DataFrame(
            {"Order": range(1, len(words) + 1), "Word": [str(w) for w in words]}
        ),
        sizing_mode="stretch_width",
        show_index=False,
        theme="default",
        pagination=None,
        layout="fit_columns",
        disabled=True,
        stylesheets=[TABLE_CSS, FIRST_COL_BOLD_CSS],
        configuration={
            "columnDefaults": {"headerSort": False},
            "columns": [
                # hozAlign='left' overrides Tabulator's default right-alignment for
                # numeric columns so Order lines up flush with the Word column.
                {"field": "Order", "widthGrow": 1, "hozAlign": "left"},
                {"field": "Word", "widthGrow": 8, "formatter": "textarea"},
            ],
        },
    )
    return pn.Column(prompt, table, sizing_mode="stretch_width", styles=card_styles())


def build_dass(row):
    dass_rows = []
    for i, factor, question in DASS_ITEMS:
        score_col = f"dass_item_{i}_score"
        expl_col = f"dass_item_{i}_explanation"
        score = (
            int(row[score_col])
            if score_col in row and pd.notna(row[score_col])
            else "—"
        )
        expl = (
            str(row[expl_col]) if expl_col in row and pd.notna(row[expl_col]) else "—"
        )
        dass_rows.append(
            {
                "Item": question,
                "Factor": FACTOR_LABEL[factor],
                "Score": score,
                "Explanation": expl,
            }
        )
    dass_table = pn.widgets.Tabulator(
        pd.DataFrame(dass_rows),
        sizing_mode="stretch_width",
        show_index=False,
        theme="default",
        pagination=None,
        layout="fit_columns",
        disabled=True,
        stylesheets=[TABLE_CSS, FIRST_COL_BOLD_CSS],
        configuration={
            "columnDefaults": {"headerWordWrap": True, "headerSort": False},
            "columns": [
                {"field": "Item", "widthGrow": 2, "formatter": "textarea"},
                {"field": "Factor", "widthGrow": 1, "headerSort": True},
                # hozAlign='left' overrides Tabulator's default right-alignment
                # for numeric columns so Score lines up with Factor / Explanation.
                {
                    "field": "Score",
                    "widthGrow": 1,
                    "headerSort": True,
                    "hozAlign": "left",
                },
                {"field": "Explanation", "widthGrow": 3, "formatter": "textarea"},
            ],
        },
    )
    return pn.Column(
        description(
            "**DASS-21 Scores & Explanations** — The Depression, Anxiety and Stress "
            "Scale: 21 items (seven per subscale), each rated 0–3 by the persona "
            "with a written justification."
        ),
        dass_table,
        sizing_mode="stretch_width",
        styles=card_styles(),
    )


# Dispatch table — used by the dashboard to render the active view layer.
BUILDERS = {"Topics": build_topics, "ERT": build_ert, "DASS-21": build_dass}
