from dataclasses import dataclass, field
from datetime import date


@dataclass
class OptionContract:
    strike: float
    expiration: date
    option_type: str  # "call" or "put"
    gamma: float | None
    delta: float | None
    vanna: float | None
    charm: float | None
    iv: float | None
    open_interest: int
    volume: int
    bid: float
    ask: float
    dte: int


@dataclass
class OptionChain:
    symbol: str
    spot_price: float
    contracts: list[OptionContract]


@dataclass
class GEXResult:
    strike: float
    call_gex: float
    put_gex: float
    net_gex: float
    abs_net_gex: float


@dataclass
class GammaLadder:
    rows: list[GEXResult]
    call_wall: float | None
    put_wall: float | None
    flip_level: float | None
    net_regime: str  # "positive" or "negative"
    vanna_exposure: float
    charm_exposure: float
