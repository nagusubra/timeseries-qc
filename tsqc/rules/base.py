"""Abstract base class for all QC rules."""

from abc import ABC, abstractmethod

import pandas as pd


class Rule(ABC):
    """Base class for all QC rules.

    Subclasses must define:
        name: str  — short identifier used in quality_reasons column
        level: str — "sus" or "bad", the quality label applied when the rule fires
    """

    name: str
    level: str

    def __init__(self, level: str = "bad") -> None:
        if level not in ("sus", "bad"):
            raise ValueError(f"level must be 'sus' or 'bad', got {level!r}")
        self.level = level

    @abstractmethod
    def check(self, series: pd.Series) -> pd.Series:
        """Return a boolean Series; True = this row is flagged by this rule.

        Args:
            series: A pandas Series of float values with a DatetimeIndex.

        Returns:
            Boolean Series aligned with the input index.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(level={self.level!r})"
