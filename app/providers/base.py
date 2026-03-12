from abc import ABC, abstractmethod

from app.models import OptionChain


class DataProvider(ABC):
    @abstractmethod
    def get_option_chain(self, symbol: str) -> OptionChain:
        ...

    @abstractmethod
    def get_spot_price(self, symbol: str) -> float:
        ...
