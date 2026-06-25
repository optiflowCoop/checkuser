"""
Engine Module: SOLID Design Patterns for License Optimization

This module contains the rule engine and optimization engine using SOLID principles.

Components:
- rules.py: UserClassificationEngine with Strategy pattern for user classification
- optimizer.py: LicenseOptimizer with Strategy pattern for license optimization

Both engines replace hardcoded if/elif blocks with extensible rule classes.
"""

from .rules import UserClassificationEngine, ClassificationRule
from .optimizer import LicenseOptimizerEngine, OptimizationRule

__all__ = [
    'UserClassificationEngine',
    'ClassificationRule',
    'LicenseOptimizer',
    'OptimizationStrategy',
]
