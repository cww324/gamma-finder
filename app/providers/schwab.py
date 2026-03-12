from datetime import date

from app.auth import get_client
from app.models import OptionChain, OptionContract
from app.providers.base import DataProvider


class SchwabProvider(DataProvider):
    def __init__(self) -> None:
        self._client = get_client()

    def get_spot_price(self, symbol: str) -> float:
        resp = self._client.get_quote(symbol)
        resp.raise_for_status()
        return float(resp.json()[symbol]["quote"]["lastPrice"])

    def get_option_chain(self, symbol: str) -> OptionChain:
        spot = self.get_spot_price(symbol)
        resp = self._client.get_option_chain(symbol)
        resp.raise_for_status()
        data = resp.json()

        contracts: list[OptionContract] = []
        for option_type, map_key in [("call", "callExpDateMap"), ("put", "putExpDateMap")]:
            for exp_strike_map in data.get(map_key, {}).values():
                for strike_str, option_list in exp_strike_map.items():
                    for o in option_list:
                        exp = date.fromisoformat(o["expirationDate"][:10])
                        contracts.append(OptionContract(
                            strike=float(strike_str),
                            expiration=exp,
                            option_type=option_type,
                            gamma=o.get("gamma"),
                            delta=o.get("delta"),
                            vanna=None,  # not provided by Schwab directly
                            charm=None,  # not provided by Schwab directly
                            iv=o.get("volatility"),
                            open_interest=int(o.get("openInterest") or 0),
                            volume=int(o.get("totalVolume") or 0),
                            bid=float(o.get("bid") or 0),
                            ask=float(o.get("ask") or 0),
                            dte=int(o.get("daysToExpiration") or 0),
                        ))

        return OptionChain(symbol=symbol, spot_price=spot, contracts=contracts)
