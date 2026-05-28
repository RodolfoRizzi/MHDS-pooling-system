"""Dashboard class + launcher.

`MHDSDashboard` is based on `SupportMe_Data_Pooling_v4.ipynb`.
"""

from __future__ import annotations

import io
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import panel as pn
from IPython.display import display

from . import data
from .config import (
    DATA_VERSION,
    FILTER_GROUPS,
    SOCIO_COLS,
    VIEW_MODES,
)
from ._ui.builders import BUILDERS, render_persona_card
from ._ui.components import (
    btn_css,
    card_styles,
    description,
    modal_header,
    section_header,
)
from ._ui.tokens import (
    ACCENT,
    BLUE_H,
    BORDER,
    EXT,
    FS_BODY,
    GLOBAL_WHITE_CSS,
    MODAL_BODY,
    MODAL_CSS,
    PAGE_BG,
    SURFACE,
    TEXT,
    TEXT_MUTED,
)


# Default placeholder for the (now mandatory) model filter. The user must pick a
# real model before a search runs — see _on_search.
MODEL_PLACEHOLDER = "Select a model"

# Browser tab / served-document title.
APP_TITLE = "MHDS Pooling System"


def _detect_colab() -> bool:
    try:
        from google.colab import drive  # noqa: F401

        return True
    except ImportError:
        return False


class MHDSDashboard(pn.viewable.Viewer):
    """Mental Health Digital Shadows dashboard."""

    def __init__(self, master_df, **params):
        super().__init__(**params)
        self.master_df = data.normalize_df(master_df)
        self.matched = None  # holds the most recent filtered DataFrame

        self._build_sidebar()
        self._build_main_widgets()
        self._build_download()
        self._build_search_modal()
        self._build_layout()
        self._wire_callbacks()

    # ── Setup ─────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        """Filter widgets grouped into collapsible cards."""
        self.socio_widgets = {}
        self.filter_cards = []
        for group_name, cols in FILTER_GROUPS.items():
            group_widgets = []
            for col in cols:
                if col in self.master_df.columns:
                    vals = sorted(
                        self.master_df[col].dropna().astype(str).unique().tolist()
                    )
                    options = (
                        [MODEL_PLACEHOLDER] + vals
                        if col == "model_name"
                        else ["Any"] + vals
                    )
                    w = pn.widgets.Select(
                        name=col.replace("_", " ").title(),
                        options=options,
                        sizing_mode="stretch_width",
                    )
                    self.socio_widgets[col] = w
                    group_widgets.append(w)
            self.filter_cards.append(
                pn.Card(
                    *group_widgets,
                    title=group_name,
                    collapsed=True,
                    sizing_mode="stretch_width",
                    styles={"background": "#ffffff", "margin-bottom": "8px"},
                )
            )

        # Precompute stringified filter columns once — avoids re-stringifying
        # 75k rows × 24 columns on every search click.
        # NaN cells stringify to 'nan'; excluded from widget options via dropna(),
        # so they only surface under 'Any'.
        self._filter_str = {
            col: self.master_df[col].astype(str).values for col in self.socio_widgets
        }

        self.btn_search = pn.widgets.Button(
            name="🔍  Search Personas",
            button_type="default",
            sizing_mode="stretch_width",
            height=42,
            stylesheets=btn_css(ACCENT, "#ffffff", BLUE_H),
        )
        self.btn_reset = pn.widgets.Button(
            name="↺  Reset All Filters",
            button_type="default",
            sizing_mode="stretch_width",
            height=42,
            margin=(10, 10, 5, 10),
            disabled=True,
            stylesheets=btn_css("#ff983d", "#ffffff", "#D35400"),
        )
        self.btn_clean = pn.widgets.Button(
            name="🧹  Clean Table & Answers",
            button_type="default",
            sizing_mode="stretch_width",
            height=42,
            margin=(0, 10, 5, 10),
            disabled=True,
            stylesheets=btn_css("#C0392B", "#ffffff", "#A93226"),
        )

    def _build_main_widgets(self):
        """View-mode toggle, status, table, card, figure area.
        Right-pane interactive widgets start `disabled=True` and are enabled
        only after a search returns at least one row."""
        self.w_layer = pn.widgets.RadioButtonGroup(
            name="View",
            options=VIEW_MODES,
            value=VIEW_MODES[0],
            button_type="primary",
            sizing_mode="stretch_width",
            disabled=True,
            stylesheets=[
                f"""
                :host {{ display:flex !important; }}
                :host .bk-btn-group {{
                    display:flex !important; gap:12px !important; width:100%;
                }}
                :host .bk-btn {{
                    flex:1 1 auto; margin:0 !important;
                    border-radius:8px !important;
                    border:1px solid {ACCENT} !important;
                    font-weight:600 !important;
                    background:{SURFACE} !important; color:{ACCENT} !important;
                }}
                :host .bk-btn.bk-active {{
                    background:{ACCENT} !important; color:#ffffff !important;
                }}
            """
            ],
        )

        self.status_pane = pn.pane.Markdown(
            "_Select a **Model Name** in **LLMs / Modality** and other **Filters** (optional), then run **Search Personas** to begin._",
            sizing_mode="stretch_width",
            styles={"font-size": FS_BODY},
        )
        # disabled=True turns off in-cell editing (same knob the DASS table uses);
        # selectable=1 keeps single-row click-selection working — they're
        # independent in Panel ≥ 1.x. on_click is wired as a belt-and-suspenders
        # fallback in case the `selection` watcher doesn't fire on a given click.
        self.persona_tbl_pane = pn.widgets.Tabulator(
            pd.DataFrame(),
            sizing_mode="stretch_width",
            max_height=300,
            theme="default",
            show_index=False,
            disabled=True,
            selectable=1,
            pagination="local",
            page_size=10,
        )
        self.persona_card_pane = pn.pane.HTML(
            "", sizing_mode="stretch_width", styles=card_styles()
        )
        # Instruction shown under "Selecting Personas" — only visible once a
        # search has populated the table (toggled in _set_results_enabled).
        self.persona_hint = description(
            "Click a persona in the **Matching Personas** table above to load the answers below."
        )
        self.persona_hint.visible = False
        self.figures_col = pn.Column(sizing_mode="stretch_width", min_height=400)

    def _build_download(self):
        """Download modal: pick format, then trigger FileDownload.
        Both the button and the underlying file widget start disabled."""
        self.w_format = pn.widgets.Select(
            name="Export format",
            options=list(EXT),
            value="XLSX",
            sizing_mode="stretch_width",
        )
        self.file_download = pn.widgets.FileDownload(
            callback=self._download_data,
            filename="pooled_personas.xlsx",
            label="⬇  Download",
            button_type="default",
            sizing_mode="stretch_width",
            height=42,
            margin=(0, 0, 0, 0),
            disabled=True,
            stylesheets=btn_css("#2ECC71", "#ffffff", "#27AE60"),
        )
        self.btn_download = pn.widgets.Button(
            name="⬇  Download",
            button_type="default",
            sizing_mode="stretch_width",
            height=42,
            disabled=True,
            stylesheets=btn_css("#2ECC71", "#ffffff", "#27AE60"),
        )
        self.download_modal = pn.Modal(
            pn.Column(
                modal_header(
                    "Download filtered pool", "Choose a format, then download."
                ),
                self.w_format,
                pn.Spacer(height=10),
                self.file_download,
                styles=MODAL_BODY,
            ),
            name="Download",
            show_close_button=True,
            stylesheets=MODAL_CSS,
        )

    def _build_search_modal(self):
        """Confirm modal shown when re-searching after a result is loaded."""
        self.btn_confirm = pn.widgets.Button(
            name="Yes, search",
            button_type="default",
            height=40,
            width=150,
            stylesheets=btn_css(ACCENT, "#ffffff", BLUE_H),
        )
        self.btn_cancel = pn.widgets.Button(
            name="Cancel",
            button_type="default",
            height=40,
            width=120,
            stylesheets=btn_css(
                "#ffffff", TEXT_MUTED, "#f1f3f5", border=f"1px solid {BORDER}"
            ),
        )
        self.search_modal = pn.Modal(
            pn.Column(
                modal_header(
                    "Start a new search?",
                    "This clears the current personas table and the loaded answers.",
                ),
                pn.Row(
                    pn.Spacer(),
                    self.btn_cancel,
                    self.btn_confirm,
                    pn.Spacer(),
                    margin=(16, 0, 0, 0),
                ),
                styles=MODAL_BODY,
            ),
            name="Confirm new search",
            show_close_button=True,
            stylesheets=MODAL_CSS,
        )

    def _build_layout(self):
        """Title bar + two-column body (sidebar + main); modals appended last."""
        title_bar = pn.pane.HTML(
            f"""
            <div style="background:{ACCENT};border-radius:12px;
                        padding:16px 22px;margin-bottom:16px;
                        display:flex;align-items:center;gap:14px;">
              <div>
                <div style="color:#fff;font-size:1.15rem;font-weight:700;
                            letter-spacing:.3px;">Mental Health Digital Shadows</div>
                <div style="color:#c5d3e0;font-size:.8rem;margin-top:2px;">
                  Data Pooling Dashboard · PENSO / SUPPORT ME</div>
              </div>
            </div>
            """,
            sizing_mode="stretch_width",
            margin=0,
        )

        body = pn.Row(
            pn.Column(
                section_header("🔎", "Filters"),
                pn.pane.HTML(
                    f'<div style="font-size:.82rem;color:{TEXT_MUTED};'
                    f'margin-bottom:10px;">Filters · <i>"Any" = no filter</i></div>',
                    margin=0,
                ),
                *self.filter_cards,
                pn.Spacer(height=8),
                self.btn_search,
                self.btn_reset,
                self.btn_clean,
                width=340,
                styles=card_styles({"padding": "18px", "margin-right": "16px"}),
                stylesheets=[GLOBAL_WHITE_CSS],
            ),
            pn.Column(
                section_header("👥", "Matching Personas"),
                self.status_pane,
                self.persona_tbl_pane,
                self.btn_download,
                pn.Spacer(height=18),
                section_header("⚙️", "Selecting Personas"),
                self.persona_hint,
                self.persona_card_pane,
                pn.Spacer(height=18),
                section_header("📊", "Answers"),
                self.w_layer,
                pn.Spacer(height=8),
                self.figures_col,
                sizing_mode="stretch_width",
                styles=card_styles({"padding": "18px"}),
                stylesheets=[GLOBAL_WHITE_CSS],
            ),
            sizing_mode="stretch_width",
        )

        self._root = pn.Column(
            title_bar,
            body,
            self.search_modal,
            self.download_modal,
            sizing_mode="stretch_width",
            styles={"background": PAGE_BG, "padding": "16px"},
            stylesheets=[GLOBAL_WHITE_CSS],
        )

    def _wire_callbacks(self):
        self.btn_search.on_click(self._on_search)
        self.btn_reset.on_click(self._on_reset)
        self.btn_clean.on_click(self._on_clean)
        self.btn_confirm.on_click(self._on_confirm)
        self.btn_cancel.on_click(self._on_cancel)
        self.btn_download.on_click(self._on_download_open)
        self.w_format.param.watch(self._on_format_change, "value")
        self.w_layer.param.watch(self._on_layer_change, "value")
        for ww in self.socio_widgets.values():
            ww.param.watch(self._update_reset_state, "value")
        self.persona_tbl_pane.param.watch(self._on_table_select, "selection")
        # Direct click event — bypasses the selection watcher, which can be
        # silent if Tabulator decides a click was a header/scroll/etc.
        self.persona_tbl_pane.on_click(self._on_table_click)

    # ── Right-pane enable/disable ─────────────────────────────────────────
    def _set_results_enabled(self, enabled):
        """Toggle the right-side interactive controls in one place.
        Called with True after a successful search, False otherwise."""
        self.w_layer.disabled = not enabled
        self.btn_download.disabled = not enabled
        self.file_download.disabled = not enabled
        self.btn_clean.disabled = not enabled
        self.persona_hint.visible = enabled

    def _update_reset_state(self, *events):
        """Enable Reset All Filters only when at least one filter differs from
        its default (model = placeholder, every other filter = 'Any')."""
        changed = any(
            ww.value != (MODEL_PLACEHOLDER if col == "model_name" else "Any")
            for col, ww in self.socio_widgets.items()
        )
        self.btn_reset.disabled = not changed

    def _clear_results(self):
        """Wipe the loaded result state: table, persona card, answers figures,
        and disable the right pane. Shared by the empty-search branch and the
        Clean Table & Answers button."""
        self.matched = None
        self.figures_col.objects = []
        self.persona_tbl_pane.value = pd.DataFrame()
        self.persona_tbl_pane.selection = []
        self.persona_card_pane.object = ""
        self._set_results_enabled(False)

    # ── Core logic ────────────────────────────────────────────────────────
    def get_matching_rows(self):
        mask = np.ones(len(self.master_df), dtype=bool)
        for col, ww in self.socio_widgets.items():
            if ww.value not in ("Any", MODEL_PLACEHOLDER):
                mask &= self._filter_str[col] == ww.value
        return self.master_df.loc[mask].reset_index(drop=True)

    def _render_card(self, idx):
        if idx is None or self.matched is None or idx >= len(self.matched):
            return ""
        return render_persona_card(self.matched.iloc[idx])

    def _render_figures(self, idx):
        """Render the Answers figure for the persona at `idx`. Safe for any
        idx in matched; used by both watcher-driven and direct-update paths."""
        if self.matched is None or idx is None or idx >= len(self.matched):
            self.figures_col.objects = []
            return
        row = self.matched.iloc[idx]
        self.figures_col.objects = [BUILDERS[self.w_layer.value](row)]

    def _show_view(self):
        """Re-render figures using the table's current selection (the canonical
        source-of-truth for the active persona)."""
        sel = self.persona_tbl_pane.selection
        idx = sel[0] if sel else None
        self._render_figures(idx)

    def _do_search(self):
        self.figures_col.objects = []
        matched = self.get_matching_rows()

        if matched.empty:
            self.status_pane.object = "⚠️ **No personas match the selected filters.**"
            self._clear_results()
            return

        self.matched = matched
        n = len(matched)
        self.status_pane.object = f"✅ **Found {n} matching personas.**"

        # Enable the right pane FIRST. Any downstream failure (e.g., a huge
        # dropdown options dict stalling Panel) must not leave the user with
        # locked Download / View buttons after a successful search.
        self._set_results_enabled(True)

        # Table — populates fine even for 75k rows (Tabulator paginates).
        display_cols = list(
            dict.fromkeys(
                ["model_name", "JSON_file"]
                + [c for c in SOCIO_COLS if c in matched.columns]
            )
        )
        numbered = matched[display_cols].copy()
        numbered.insert(0, "#", range(1, n + 1))
        self.persona_tbl_pane.value = numbered

        # Card + figures for row 0 — direct, no watcher round-trip.
        self.persona_card_pane.object = render_persona_card(matched.iloc[0])
        self._render_figures(0)
        self.persona_tbl_pane.selection = [0]

    def _download_data(self):
        df = self.matched if self.matched is not None else self.get_matching_rows()
        fmt = self.w_format.value
        buf = io.BytesIO()
        if fmt == "XLSX":
            df.to_excel(buf, index=False, engine="openpyxl")
        else:
            df.to_pickle(buf)
        buf.seek(0)
        return buf

    # ── Event handlers ────────────────────────────────────────────────────
    def _on_search(self, event):
        if self.socio_widgets["model_name"].value == MODEL_PLACEHOLDER:
            self.status_pane.object = (
                "⚠️ **Please select a Model Name in LLMs / Modality before searching.**"
            )
            return
        if self.matched is not None:
            self.search_modal.open = True
        else:
            self._do_search()

    def _on_confirm(self, event):
        self.search_modal.open = False
        self._do_search()

    def _on_cancel(self, event):
        self.search_modal.open = False

    def _on_reset(self, event):
        """Reset filters to their defaults but keep result panel state untouched —
        the user may still want to review what they had."""
        for col, ww in self.socio_widgets.items():
            ww.value = MODEL_PLACEHOLDER if col == "model_name" else "Any"
        self.status_pane.object = "_Filters reset — select a **Model Name** in **LLMs / Modality** and other **Filters** (optional), then run **Search Personas** to start a new search._"

    def _on_clean(self, event):
        """Clear the loaded personas table and answers so a fresh search can run."""
        self._clear_results()
        self.status_pane.object = "_Cleared — change **Filters** (optional) and run **Search Personas** to start a new search._"

    def _on_table_select(self, event):
        """`selection` property changed → drive card + figures."""
        if not event.new:
            return
        idx = event.new[0]
        if self.matched is None or idx >= len(self.matched):
            return
        self.persona_card_pane.object = self._render_card(idx)
        self._render_figures(idx)

    def _on_table_click(self, event):
        """Raw cell-click event → drive selection via row index.
        Fires for every cell click; `event.row` is the absolute row index in
        `self.matched`, regardless of pagination."""
        if event.row is None or self.matched is None:
            return
        if self.persona_tbl_pane.selection != [event.row]:
            self.persona_tbl_pane.selection = [event.row]

    def _on_layer_change(self, event):
        self._show_view()

    def _on_download_open(self, event):
        self.download_modal.open = True

    def _on_format_change(self, event):
        self.file_download.filename = f"pooled_personas.{EXT[event.new]}"

    # ── Viewer protocol ───────────────────────────────────────────────────
    def __panel__(self):
        return self._root


# ── Launcher ──────────────────────────────────────────────────────────────
def launch_dashboard(
    df: pd.DataFrame | None = None,
    data_version: str = DATA_VERSION,
    cache_dir: str | Path | None = None,
):
    """Launch the dashboard.

    - In Colab: inline-displays the Viewer via display(pn.panel(app)).
    - Locally: calls app.show() to open a browser tab on Panel's built-in server.
    - If `df` is provided, skips the download/load and reuses it.

    Does not return the Viewer. Returning it would let Colab's auto-display
    render the cell value, mounting a second copy of the same Viewer in the
    document — that triggers `Models must be owned by only a single document`
    on the next callback. Equivalent of v6_2's cell 8 (side-effect-only).
    """
    warnings.filterwarnings("ignore")

    in_colab = _detect_colab()
    pn.extension(
        "tabulator",
        "modal",
        comms="colab" if in_colab else "default",
        sizing_mode="stretch_width",
    )

    if df is None:
        df = data.load_pool(data_version=data_version, cache_dir=cache_dir)

    app = MHDSDashboard(df)

    if in_colab:
        app.servable(title=APP_TITLE)
        display(pn.panel(app))
    else:
        app.show(title=APP_TITLE)
