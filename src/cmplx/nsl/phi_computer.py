"""cqe.core.phi — phi computation."""
import math

PHI = (1 + math.sqrt(5)) / 2

class PhiComputer:
    def compute(self, value, **kw): return value * PHI
    def normalize(self, value): return value / PHI if value != 0 else 0
