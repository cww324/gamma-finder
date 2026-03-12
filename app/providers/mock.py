import json
from datetime import date
from pathlib import Path

from app.models import OptionChain, OptionContract
from app.providers.base import DataProvider

FIXTURE_PATH = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "spy_chain.json"


class MockProvider(DataProvider):
    def __init__(self, fixture_path: Path = FIXTURE_PATH) -> None:
        with open(fixture_path) as f:
            self._data = json.load(f)

    def get_spot_price(self, symbol: str) -> float:
        return float(self._data["spot_price"])

    def get_option_chain(self, symbol: str) -> OptionChain:
        contracts = [
            OptionContract(
                strike=float(c["strike"]),
                expiration=date.fromisoformat(c["expiration"]),
                option_type=c["option_type"],
                gamma=c.get("gamma"),
                delta=c.get("delta"),
                vanna=c.get("vanna"),
                charm=c.get("charm"),
                iv=c.get("iv"),
                open_interest=int(c.get("open_interest") or 0),
                volume=int(c.get("volume") or 0),
                bid=float(c.get("bid") or 0),
                ask=float(c.get("ask") or 0),
                dte=int(c.get("dte") or 0),
            )
            for c in self._data["contracts"]
        ]
        return OptionChain(
            symbol=self._data["symbol"],
            spot_price=self._data["spot_price"],
            contracts=contracts,
        )
