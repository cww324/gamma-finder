import argparse
import os

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gamma Finder — dealer GEX terminal dashboard")
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--0dte", dest="zero_dte", action="store_true", help="Start in 0DTE view")
    parser.add_argument("--max-dte", type=int, default=None, help="Filter contracts to max DTE")
    parser.add_argument("--refresh", type=int, default=60, help="Auto-refresh interval in seconds (default: 60)")
    parser.add_argument("--export", default=None, help="Export ladder to CSV path on startup")
    parser.add_argument("--weighted", action="store_true", help="Use delta-weighted GEX (non-standard heuristic)")
    parser.add_argument("--compact", action="store_true", help="Compact display mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    provider_name = os.getenv("DATA_PROVIDER", "mock").lower()

    if provider_name == "schwab":
        from app.providers.schwab import SchwabProvider
        provider = SchwabProvider()
    else:
        from app.providers.mock import MockProvider
        provider = MockProvider()

    from app.terminal_ui import GammaFinderApp

    app = GammaFinderApp(
        provider=provider,
        symbol=args.symbol.upper(),
        refresh_interval=args.refresh,
        weighted=args.weighted,
    )
    app.title = f"Gamma Finder — {args.symbol.upper()}"
    app.run()


if __name__ == "__main__":
    main()
