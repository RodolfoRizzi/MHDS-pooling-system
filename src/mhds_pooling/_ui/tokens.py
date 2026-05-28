"""Design tokens, colour palette, font sizes, and CSS strings.

Verbatim port of the top of cell 6 in SupportMe_Data_Pooling_v6_2.ipynb
(through the MODAL_BODY constant). No values changed.
"""
from __future__ import annotations

# ── Design tokens ─────────────────────────────────────────────────────────
ACCENT     = '#2E86C1'
SURFACE    = '#ffffff'
BORDER     = '#dde4ec'
TEXT       = '#222222'
TEXT_MUTED = '#6b7682'
PAGE_BG    = '#f5f6f8'
BLUE_H     = '#256fa3'

# Keys here MUST match keys in FILTER_GROUPS (constants module). If you rename
# a group there (e.g. 'Demographic' → 'Demographics'), update it here too —
# render_persona_card iterates GROUP_COLORS and does FILTER_GROUPS[group], so a
# mismatch raises KeyError mid-render and silently aborts _do_search.
GROUP_COLORS = {
    'Demographics':          '#C0392B',
    'Job & Education':       '#1E8449',
    'Psychological Profile': '#2E86C1',
}

EXT = {'XLSX': 'xlsx', 'PKL': 'pkl'}

# ── Typography scale ──────────────────────────────────────────────────────
# Centralised so headers and body text stay in sync. Tweak here, not at each
# call site. Used by section_header / modal_header / description in components.
FS_H1 = '1.15rem'   # Title bar — "Mental Health Digital Shadows"
FS_H2 = '1.05rem'   # Section headers — "Filters", "Matching Personas", etc.
FS_H3 = '1.05rem'   # Modal titles
FS_BODY = '0.95rem'  # Description / caption text under section headers
FS_SMALL = '0.82rem'  # Hints — "Filters · 'Any' = no filter"


# ── Bare CSS strings & stylesheet lists (used by widgets) ─────────────────
BTN_SHAPE = ["""
    :host .bk-btn { border-radius:8px !important; font-weight:600 !important; }
"""]

GLOBAL_WHITE_CSS = """
:host, :host * { color: #222222; }
:host .bk-panel-models-markup-HTML,
:host .markdown, :host .markdown * { color: #222222 !important; }
"""

TABLE_CSS = """
:host .tabulator,
:host .tabulator-tableholder { background-color:#ffffff !important; }
"""

# Bold the leftmost-meaningful column in each Answers table so the row's
# "key" stands out from the supporting fields. Field names are matched by the
# Tabulator data attribute, so this rule applies wherever a table has a
# Topic / Order / Item column.
FIRST_COL_BOLD_CSS = """
:host .tabulator-cell[tabulator-field="Topic"],
:host .tabulator-cell[tabulator-field="Order"],
:host .tabulator-cell[tabulator-field="Item"] { font-weight:700 !important; }
"""

MODAL_CSS = ["""
    :host {
        background: #ffffff !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    :host .card-header-row, :host .bk-header {
        background: #ffffff !important;
        border-bottom: none !important;
    }
"""]

MODAL_BODY = {'background': SURFACE, 'padding': '20px 20px 10px 20px', 'border-radius': '8px'}
