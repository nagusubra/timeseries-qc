"""Abstract base class for all QC rules."""

from abc import ABC, abstractmethod

import numpy as np
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

    def get_reason(self, series: pd.Series, idx: int) -> str:
        """Return the reason string for a flagged row at the given index.

        Override this method to include contextual information (e.g., the actual
        value that triggered the rule). The default implementation returns the
        rule's name attribute.

        Args:
            series: The full value Series being checked.
            idx: Integer position (iloc) of the flagged row.

        Returns:
            Reason string to be added to the quality_reasons column.
        """
        return self.name

    def get_reasons_vectorized(self, series: pd.Series, mask: np.ndarray) -> np.ndarray:
        """Return an object array of reason strings aligned with *series*.

        Entries are the rule reason where *mask* is True, otherwise ``""``.
        Override for rules whose reason depends on the row value. The default
        fills ``self.name`` for every flagged position (matches ``get_reason``).
        """
        out = np.full(len(series), "", dtype=object)
        if mask.any():
            out[mask] = self.name
        return out

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(level={self.level!r})"
