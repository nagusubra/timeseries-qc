"""
tsqc — timeseries quality control library.

Public API:
    check(df, ...) -> QCResult
    QCResult
    NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule
"""

from tsqc.checker import check
from tsqc.result import QCResult
from tsqc.rules.builtins import CustomRule, DeltaRule, FlatlineRule, NullRule, OutlierRule, RangeRule

__version__ = "0.4.1"
__all__ = [
    "check",
    "QCResult",
    "NullRule",
    "FlatlineRule",
    "DeltaRule",
    "RangeRule",
    "OutlierRule",
    "CustomRule",
]
