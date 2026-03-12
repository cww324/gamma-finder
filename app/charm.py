from app.models import OptionChain


def calculate_charm_exposure(chain: OptionChain) -> float:
    total = 0.0
    for c in chain.contracts:
        charm = c.charm or 0.0
        total += charm * c.open_interest * 100
    return total
