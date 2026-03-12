from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from app.calculations import run_calculations
from app.models import GammaLadder, OptionChain
from app.providers.base import DataProvider


class MetricsPanel(Static):
    def update_ladder(self, chain: OptionChain, ladder: GammaLadder) -> None:
        spot = chain.spot_price
        regime_color = "green" if ladder.net_regime == "positive" else "red"
        self.update(
            f"Spot: [bold]{spot:.2f}[/bold]  "
            f"Regime: [{regime_color}]{ladder.net_regime.upper()}[/{regime_color}]  "
            f"Flip: [yellow]{ladder.flip_level:.2f}[/yellow]  "
            f"Call Wall: [green]{ladder.call_wall}[/green]  "
            f"Put Wall: [red]{ladder.put_wall}[/red]  "
            f"Vanna: {ladder.vanna_exposure:,.0f}  "
            f"Charm: {ladder.charm_exposure:,.0f}"
            if ladder.flip_level is not None
            else f"Spot: [bold]{spot:.2f}[/bold]  "
            f"Regime: [{regime_color}]{ladder.net_regime.upper()}[/{regime_color}]  "
            f"Flip: [dim]N/A[/dim]  "
            f"Call Wall: [green]{ladder.call_wall}[/green]  "
            f"Put Wall: [red]{ladder.put_wall}[/red]  "
            f"Vanna: {ladder.vanna_exposure:,.0f}  "
            f"Charm: {ladder.charm_exposure:,.0f}"
        )


class GammaTable(DataTable):
    def populate(self, ladder: GammaLadder, spot: float) -> None:
        self.clear(columns=True)
        self.add_columns("Strike", "Call GEX", "Put GEX", "Net GEX", "|Net GEX|")
        for row in ladder.rows:
            is_spot = abs(row.strike - spot) < 2.5
            is_call_wall = row.strike == ladder.call_wall
            is_put_wall = row.strike == ladder.put_wall

            strike_label = f"{row.strike:.1f}"
            if is_spot:
                strike_label = f"► {strike_label}"
            if is_call_wall:
                strike_label = f"[green]{strike_label} ▲[/green]"
            elif is_put_wall:
                strike_label = f"[red]{strike_label} ▼[/red]"

            net_color = "green" if row.net_gex >= 0 else "red"
            self.add_row(
                strike_label,
                f"{row.call_gex:,.0f}",
                f"{row.put_gex:,.0f}",
                f"[{net_color}]{row.net_gex:,.0f}[/{net_color}]",
                f"{row.abs_net_gex:,.0f}",
            )


class GammaFinderApp(App):
    BINDINGS = [
        Binding("s", "prompt_symbol", "Symbol"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("0", "toggle_0dte", "0DTE"),
        Binding("e", "export_csv", "Export"),
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    MetricsPanel {
        height: 3;
        padding: 0 1;
        background: $surface;
        border: solid $primary;
    }
    GammaTable {
        height: 1fr;
    }
    """

    def __init__(
        self,
        provider: DataProvider,
        symbol: str,
        refresh_interval: int,
        weighted: bool,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._provider = provider
        self._symbol = symbol
        self._refresh_interval = refresh_interval
        self._weighted = weighted
        self._chain: OptionChain | None = None
        self._ladders: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield MetricsPanel(id="metrics")
        with TabbedContent():
            with TabPane("Full", id="tab-full"):
                yield GammaTable(id="table-full")
            with TabPane("0DTE", id="tab-0dte"):
                yield GammaTable(id="table-0dte")
            with TabPane("Near-term", id="tab-nearterm"):
                yield GammaTable(id="table-nearterm")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(self._refresh_interval, self.action_refresh_data)
        self.call_after_refresh(self.action_refresh_data)

    def action_refresh_data(self) -> None:
        self._chain = self._provider.get_option_chain(self._symbol)
        self._ladders = run_calculations(self._chain, weighted=self._weighted)
        self._render_all()

    def _render_all(self) -> None:
        if not self._chain or not self._ladders:
            return
        spot = self._chain.spot_price
        metrics = self.query_one("#metrics", MetricsPanel)
        metrics.update_ladder(self._chain, self._ladders["full"])
        for key, table_id in [("full", "#table-full"), ("0dte", "#table-0dte"), ("nearterm", "#table-nearterm")]:
            table = self.query_one(table_id, GammaTable)
            table.populate(self._ladders[key], spot)

    def action_prompt_symbol(self) -> None:
        self.app.push_screen(SymbolScreen(self._symbol), self._on_symbol_changed)

    def _on_symbol_changed(self, symbol: str) -> None:
        if symbol:
            self._symbol = symbol.upper()
            self.title = f"Gamma Finder — {self._symbol}"
            self.action_refresh_data()

    def action_toggle_0dte(self) -> None:
        self.query_one(TabbedContent).active = "tab-0dte"

    def action_export_csv(self) -> None:
        if not self._ladders:
            return
        tabbed = self.query_one(TabbedContent)
        active = tabbed.active.replace("tab-", "")
        ladder = self._ladders.get(active, self._ladders["full"])
        filename = f"{self._symbol}_{active}_gex.csv"
        with open(filename, "w") as f:
            f.write("strike,call_gex,put_gex,net_gex,abs_net_gex\n")
            for row in ladder.rows:
                f.write(f"{row.strike},{row.call_gex},{row.put_gex},{row.net_gex},{row.abs_net_gex}\n")
        self.notify(f"Exported to {filename}")


class SymbolScreen(App):
    def __init__(self, current: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._current = current

    def compose(self) -> ComposeResult:
        yield Label(f"Current symbol: {self._current}\nEnter new symbol:")
        yield Input(placeholder="e.g. QQQ", id="symbol-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip().upper())
