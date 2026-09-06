import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import power_analysis as pa


def test_sample_size_reference_case():
    # p1=0.10, p2=0.15, alpha=0.05, power=0.80 -> verified by direct
    # calculation (normal-approximation two-proportion z-test formula)
    n = pa.sample_size_two_prop(0.10, 0.15)
    assert 670 <= n <= 700


def test_larger_pp_lift_needs_smaller_sample():
    n_small_lift = pa.sample_size_two_prop(0.11, 0.14)   # 3pp
    n_large_lift = pa.sample_size_two_prop(0.11, 0.19)   # 8pp
    assert n_large_lift < n_small_lift


def test_backlog_scale_threshold_sample_size():
    # The existing experimentation backlog's own numbers: baseline 11%,
    # scale threshold +8pp (-> 19%). Verified by hand: ~312/arm.
    n = pa.sample_size_two_prop(0.11, 0.19)
    assert 300 <= n <= 325


def test_mde_increases_with_smaller_sample():
    mde_small_n = pa.mde_two_prop(15, 0.11)
    mde_large_n = pa.mde_two_prop(119, 0.11)
    assert mde_small_n > mde_large_n


def test_mde_roundtrips_into_sample_size():
    # If N gives you MDE m, then the sample size required to detect
    # exactly m should be close to N (within rounding of the search).
    n_per_arm = 100
    mde = pa.mde_two_prop(n_per_arm, 0.11)
    n_check = pa.sample_size_two_prop(0.11, 0.11 + mde)
    assert abs(n_check - n_per_arm) <= 2


def test_monthly_volume_projection():
    # 9.9 leads/month for 12 months should project to ~119, split ~59.5/arm
    total, per_arm = pa.project_volume(monthly_rate=9.9, months=12)
    assert 118 <= total <= 120
    assert 59 <= per_arm <= 60
