import numpy as np

from app.models import OptionChain


def find_gamma_flip(chain: OptionChain, spot: float) -> float | None:
    grid = np.arange(spot * 0.97, spot * 1.03 + 0.5, 0.5)
    net_gex_values = []

    for price in grid:
        net = 0.0
        for c in chain.contracts:
            gamma = c.gamma or 0.0
            oi = c.open_interest or 0
            gex = gamma * oi * 100 * price ** 2
            net += gex if c.option_type == "call" else -gex
        net_gex_values.append(net)

    for i in range(len(net_gex_values) - 1):
        a, b = net_gex_values[i], net_gex_values[i + 1]
        if a == 0.0:
            return float(grid[i])
        if a * b < 0:
            # linear interpolation
            t = a / (a - b)
            return float(grid[i] + t * (grid[i + 1] - grid[i]))

    return None
