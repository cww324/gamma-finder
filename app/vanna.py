from app.models import OptionChain


def calculate_vanna_exposure(chain: OptionChain) -> float:
    spot = chain.spot_price
    total = 0.0
    for c in chain.contracts:
        vanna = c.vanna or 0.0
        iv = c.iv or 0.0
        total += vanna * c.open_interest * 100 * spot * iv
    return total
