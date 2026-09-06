"""Generic two-proportion power analysis: sample size, minimum detectable
effect (MDE), and volume projection. No Fireclay-specific assumptions --
takes baseline rates and monthly volume as arguments, so it applies to
any experiment feasibility check, not just this project's trade-show
nudge hypothesis."""
import math
from scipy import stats


def sample_size_two_prop(p1: float, p2: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Required sample size per arm to detect p2 vs p1 (two-sided z-test)."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    p_bar = (p1 + p2) / 2
    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    denominator = (p1 - p2) ** 2
    return numerator / denominator


def mde_two_prop(n_per_arm: float, p1: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Minimum detectable lift (in absolute proportion) given a fixed
    per-arm sample size, via binary search over sample_size_two_prop."""
    lo, hi = 0.0001, 0.9 - p1
    for _ in range(100):
        mid = (lo + hi) / 2
        n_needed = sample_size_two_prop(p1, p1 + mid, alpha, power)
        if n_needed > n_per_arm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def project_volume(monthly_rate: float, months: float) -> tuple:
    """Total eligible population and per-arm size (50/50 split) projected
    over a test window, given a historical monthly arrival rate."""
    total = monthly_rate * months
    return total, total / 2
