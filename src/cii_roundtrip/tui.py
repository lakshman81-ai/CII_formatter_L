from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, RadioSet, RadioButton, DataTable, RichLog
from textual.reactive import reactive

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cii_roundtrip.parser import Parser
from src.cii_roundtrip.export_csv import generate_custom_csv
from src.cii_roundtrip.logger import Logger

class DashboardApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #main_area {
        height: 60%;
        layout: horizontal;
    }

    #config_panel {
        width: 30%;
        border: solid green;
        padding: 1;
    }

    #preview_panel {
        width: 70%;
        border: solid blue;
        padding: 1;
    }

    #log_panel {
        height: 35%;
        border: solid yellow;
        padding: 1;
    }

    .title {
        text-style: bold;
        color: magenta;
    }

    Input {
        margin-bottom: 1;
    }

    Button {
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("l", "load_file", "Load & Parse File"),
        ("e", "export_csv", "Export Custom CSV")
    ]

    # Reactive state
    # Default to SAMPLE 2/BENCHMARK.CII relative to project root for ease of testing
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _default_path = os.path.join(_base_dir, "SAMPLE 2", "BENCHMARK.CII")

    filepath = reactive(_default_path)
    n1_alloc = reactive(2000)
    parsed_data = None
    logger = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="main_area"):
            with VerticalScroll(id="config_panel"):
                yield Static("FILE SETTINGS & MEMORY", classes="title")
                yield Input(placeholder="Path to .cii", value=self.filepath, id="input_file")
                yield Input(placeholder="N1 Allocation", value=str(self.n1_alloc), id="input_n1")

                yield Static("Parsing Mode:", classes="title")
                with RadioSet(id="mode_select"):
                    yield RadioButton("Standard Neutral File", value=True)
                    yield RadioButton("Data Matrix")

                yield Button("Load & Parse File", id="btn_load", variant="primary")
                yield Button("Export Custom CSV", id="btn_export", variant="success")

                yield Static("\nver.14-03-24 time 11.30", id="version_label", style="dim")

            with VerticalScroll(id="preview_panel"):
                yield Static("ELEMENTS PREVIEW", classes="title")
                yield DataTable(id="dt_preview")

        with VerticalScroll(id="log_panel"):
            yield Static("DEBUG & CONSOLE LOGGING", classes="title")
            yield RichLog(id="rich_log", highlight=True, markup=True)

        yield Footer()

    def on_mount(self) -> None:
        self.logger = Logger(feature="tui")
        self._append_log("[bold green][INFO][/] UI initialized. Ready to transfer 100% of the _A file data.")

        # Init DataTable
        dt = self.query_one("#dt_preview", DataTable)
        dt.add_columns("#", "Type", "TEXT", "DELTA X", "DELTA Y", "DELTA Z", "BEND_PTR", "SUPPORT_PTR")

    def _append_log(self, text: str):
        rich_log = self.query_one("#rich_log", RichLog)
        rich_log.write(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_load":
            self.action_load_file()
        elif event.button.id == "btn_export":
            self.action_export_csv()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input_file":
            self.filepath = event.value
        elif event.input.id == "input_n1":
            try:
                self.n1_alloc = int(event.value)
            except ValueError:
                pass

    def action_load_file(self) -> None:
        self._append_log(f"[bold blue][EVENT][/] Loading file: {self.filepath}")
        self._append_log(f"[bold magenta][MEMORY][/] N1 allocated at {self.n1_alloc}. N2 limit is {self.n1_alloc//2}.")

        try:
            p = Parser(filepath=self.filepath, n1_allocation=self.n1_alloc)
            self.parsed_data = p.parse()
            self._append_log(f"[bold cyan][PARSE][/] Successfully parsed {len(self.parsed_data.elements)} elements.")
            self.update_preview()
        except Exception as e:
            self._append_log(f"[bold red][ERROR][/] Failed to parse: {str(e)}")

    def update_preview(self) -> None:
        if not self.parsed_data: return
        dt = self.query_one("#dt_preview", DataTable)
        dt.clear()

        for i, el in enumerate(self.parsed_data.elements[:50]): # preview first 50
            from_n = el.rel[0] if len(el.rel)>0 else 0
            to_n = el.rel[1] if len(el.rel)>1 else 0
            dx = el.rel[2] if len(el.rel)>2 else 0
            dy = el.rel[3] if len(el.rel)>3 else 0
            dz = el.rel[4] if len(el.rel)>4 else 0
            bend = el.iel[0] if len(el.iel)>0 else 0
            sup = el.iel[3] if len(el.iel)>3 else 0

            comp_type = "Pipe"
            if bend > 0: comp_type = "Bend"
            elif sup > 0: comp_type = "Support"

            dt.add_row(
                str(i+1),
                comp_type,
                f"{comp_type} {from_n}-{to_n}",
                f"{dx:.2f}", f"{dy:.2f}", f"{dz:.2f}",
                str(bend), str(sup)
            )

        self._append_log("[bold green][INFO][/] Elements Preview updated.")

    def action_export_csv(self) -> None:
        if not self.parsed_data:
            self._append_log("[bold yellow][WARN][/] No data loaded. Please load a file first.")
            return

        export_path = "custom_pipeline_export.csv"
        self._append_log(f"[bold blue][EXPORT][/] Initializing Custom Pipeline 41-Column CSV routing to {export_path}...")
        try:
            generate_custom_csv(self.parsed_data, export_path=export_path)
            self._append_log("[bold green][SUCCESS][/] CSV Exported Successfully.")
        except Exception as e:
            self._append_log(f"[bold red][ERROR][/] Failed to export CSV: {str(e)}")

if __name__ == "__main__":
    app = DashboardApp()
    app.run()