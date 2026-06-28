import pytest
from app.modules.trigger.delay import calculate_delay


class TestCalculateDelay:
    def test_delay_within_range(self):
        delay = calculate_delay(2.0, 5.0)
        assert 2.0 <= delay <= 5.0

    def test_delay_disabled(self):
        delay = calculate_delay(2.0, 5.0, enabled=False)
        assert delay == 0.0

    def test_min_equals_max(self):
        delay = calculate_delay(3.0, 3.0)
        assert delay == 3.0

    def test_multiple_calls_different(self):
        # With a wide range, multiple calls should produce different values
        delays = [calculate_delay(1.0, 100.0) for _ in range(10)]
        # At least 2 different values (probability of all same is negligible)
        assert len(set(delays)) > 1

    def test_single_value_range(self):
        delay = calculate_delay(5.0, 5.0)
        assert isinstance(delay, float)
        assert delay == 5.0
