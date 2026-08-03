"""
tsqc — timeseries quality control library.

Public API:
    check(df, ...) -> QCResult
    QCResult
    NullRule, FlatlineRule, DeltaRule, RangeRule, CustomRule
"""

from tsqc.brand import logo_bytes, logo_svg
from tsqc.checker import check
from tsqc.result import QCResult
from tsqc.rules.builtins import (
    CustomRule,
    DeltaRule,
    FlatlineRule,
    NullRule,
    OutlierRule,
    RangeRule,
)

__version__ = "0.5.0"
__all__ = [
    "QCResult",
    "check",
    "CustomRule",
    "DeltaRule",
    "FlatlineRule",
    "NullRule",
    "OutlierRule",
    "RangeRule",
    "logo_bytes",
    "logo_svg",
]
