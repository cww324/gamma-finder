from app.charm import calculate_charm_exposure
from app.flip import find_gamma_flip
from app.gamma import build_gamma_ladder
from app.models import GammaLadder, OptionChain
from app.vanna import calculate_vanna_exposure


def run_calculations(chain: OptionChain, weighted: bool = False) -> dict[str, GammaLadder]:
    vanna = calculate_vanna_exposure(chain)
    charm = calculate_charm_exposure(chain)
    flip = find_gamma_flip(chain, chain.spot_price)

    subsets = {
        "full": chain.contracts,
        "0dte": [c for c in chain.contracts if c.dte == 0],
        "nearterm": [c for c in chain.contracts if c.dte <= 2],
    }

    result = {}
    for key, contracts in subsets.items():
        sub_chain = OptionChain(
            symbol=chain.symbol,
            spot_price=chain.spot_price,
            contracts=contracts,
        )
        rows = build_gamma_ladder(sub_chain, weighted=weighted)

        if rows:
            call_wall = max(rows, key=lambda r: r.net_gex).strike
            put_wall = min(rows, key=lambda r: r.net_gex).strike
            net_regime = "positive" if sum(r.net_gex for r in rows) > 0 else "negative"
        else:
            call_wall = None
            put_wall = None
            net_regime = "positive"

        result[key] = GammaLadder(
            rows=rows,
            call_wall=call_wall,
            put_wall=put_wall,
            flip_level=flip,
            net_regime=net_regime,
            vanna_exposure=vanna,
            charm_exposure=charm,
        )

    return result
