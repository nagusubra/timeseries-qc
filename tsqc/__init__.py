"""
tsqc — timeseries quality control library.

Public API:
    check(df, ...) -> QCResult
    QCResult
    NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule
"""

from tsqc.checker import check
from tsqc.result import QCResult
from tsqc.rules.builtins import CustomRule, DeltaRule, FlatlineRule, NullRule, RangeRule

__version__ = "0.1.0"
__all__ = [
    "check",
    "QCResult",
    "NullRule",
    "FlatlineRule",
    "DeltaRule",
    "RangeRule",
    "CustomRule",
]
