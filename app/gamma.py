import pandas as pd

from app.models import GEXResult, OptionChain


def build_gamma_ladder(chain: OptionChain, weighted: bool = False) -> list[GEXResult]:
    spot = chain.spot_price
    rows = []
    for c in chain.contracts:
        gamma = c.gamma or 0.0
        oi = c.open_interest or 0
        delta = c.delta or 0.0
        gex = gamma * oi * 100 * spot ** 2
        if weighted:
            gex *= abs(delta)
        rows.append({"strike": c.strike, "option_type": c.option_type, "gex": gex})

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df["gex"] = df["gex"].fillna(0.0)

    calls = df[df["option_type"] == "call"].groupby("strike")["gex"].sum().rename("call_gex")
    puts = df[df["option_type"] == "put"].groupby("strike")["gex"].sum().rename("put_gex")

    ladder = pd.concat([calls, puts], axis=1).fillna(0.0).sort_index()
    ladder["net_gex"] = ladder["call_gex"] - ladder["put_gex"]
    ladder["abs_net_gex"] = ladder["net_gex"].abs()

    return [
        GEXResult(
            strike=float(strike),
            call_gex=float(row["call_gex"]),
            put_gex=float(row["put_gex"]),
            net_gex=float(row["net_gex"]),
            abs_net_gex=float(row["abs_net_gex"]),
        )
        for strike, row in ladder.iterrows()
    ]
