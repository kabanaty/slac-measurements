import pytest

from slac_measurements.wires.collection.buffer import (
    _calculate_buffer_points,
    buffer_limit_for_beampath,
    calculate_optimal_scan_pulses,
)


class TestCalculateBufferPoints:
    """Verify the refactored _calculate_buffer_points still produces expected values."""

    def test_historical_mode(self):
        assert _calculate_buffer_points(350, 120) == 1453

    def test_high_rate_mode(self):
        result = _calculate_buffer_points(5000, 16000)
        assert result == 19166

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            _calculate_buffer_points(350, 0)

    def test_none_rate_raises(self):
        with pytest.raises(ValueError):
            _calculate_buffer_points(350, None)


class TestBufferLimitForBeampath:
    def test_cu_hxr(self):
        assert buffer_limit_for_beampath("CU_HXR") == 2800

    def test_cu_sxr(self):
        assert buffer_limit_for_beampath("CU_SXR") == 2800

    def test_sc_hxr(self):
        assert buffer_limit_for_beampath("SC_HXR") == 20000

    def test_sc_bsyd(self):
        assert buffer_limit_for_beampath("SC_BSYD") == 20000


class TestCalculateOptimalScanPulses:
    def test_nc_120hz(self):
        """At 120 Hz with NC buffer limit, resolution target dominates."""
        result = calculate_optimal_scan_pulses(120, "CU_HXR")
        assert result == 364  # ceil(4000 / 11)
        assert _calculate_buffer_points(result, 120) <= 2800

    def test_sc_high_rate(self):
        """At 16 kHz, speed constraint forces higher pulses."""
        result = calculate_optimal_scan_pulses(16000, "SC_HXR")
        assert _calculate_buffer_points(result, 16000) <= 20000
        # Speed lower bound: ceil(16000 * 4000 / 30000) = 2134
        assert result >= 2134

    def test_speed_min_caps_low_rate(self):
        """At very low rates, speed_min limits pulses below target resolution."""
        result = calculate_optimal_scan_pulses(60, "CU_HXR")
        # max_pulses_speed = int(60 * 4000 / 1000) = 240
        assert result == 240

    def test_mps_speed_constrains(self):
        """When MPS speed is high, it limits max pulses."""
        result = calculate_optimal_scan_pulses(120, "CU_HXR", speed_min=5000.0)
        # max_pulses_speed = int(120 * 4000 / 5000) = 96
        assert result <= 96

    def test_infeasible_raises(self):
        """When constraints conflict, raises ValueError."""
        with pytest.raises(ValueError):
            calculate_optimal_scan_pulses(120, "CU_HXR", speed_max=500.0)

    def test_invalid_beam_rate(self):
        with pytest.raises(ValueError):
            calculate_optimal_scan_pulses(0, "CU_HXR")

    def test_speed_min_gte_speed_max(self):
        with pytest.raises(ValueError):
            calculate_optimal_scan_pulses(
                120, "CU_HXR", speed_min=30000.0, speed_max=1000.0
            )

    def test_custom_range(self):
        """Custom range_distance changes the result."""
        result = calculate_optimal_scan_pulses(120, "CU_HXR", range_distance=8000)
        assert _calculate_buffer_points(result, 120) <= 2800

    def test_custom_resolution(self):
        """Custom target_resolution changes result at low rates."""
        result = calculate_optimal_scan_pulses(120, "CU_HXR", target_resolution=20.0)
        assert result == 200  # ceil(4000 / 20)
