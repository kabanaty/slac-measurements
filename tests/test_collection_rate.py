from unittest import TestCase
from unittest.mock import MagicMock, patch

from slac_measurements.wires.collection.base import BaseWireMeasurementCollection
from slac_measurements.wires.collection.buffer import reserve_buffer


class _Collection:
    """Stand-in exposing only what the rate helpers read."""

    _effective_beam_rate = BaseWireMeasurementCollection._effective_beam_rate
    _calculate_acquisition_timeout_s = (
        BaseWireMeasurementCollection._calculate_acquisition_timeout_s
    )

    def __init__(self, beam_rate, rate_limit_hz, n_measurements):
        self.beam_profile_device = MagicMock(beam_rate=beam_rate)
        self.buffer = MagicMock(
            rate_limit_hz=rate_limit_hz, n_measurements=n_measurements
        )


def _make_collection(beam_rate=120, rate_limit_hz=None, n_measurements=1600):
    return _Collection(beam_rate, rate_limit_hz, n_measurements)


class EffectiveBeamRateTest(TestCase):
    def test_no_rate_limit_uses_beam_rate(self):
        self.assertEqual(_make_collection()._effective_beam_rate(), 120)

    def test_rate_limit_caps_beam_rate(self):
        collection = _make_collection(rate_limit_hz=30.0)
        self.assertEqual(collection._effective_beam_rate(), 30.0)

    def test_rate_limit_above_beam_rate_ignored(self):
        collection = _make_collection(beam_rate=10, rate_limit_hz=30.0)
        self.assertEqual(collection._effective_beam_rate(), 10)

    def test_buffer_without_rate_limit_attribute(self):
        collection = _make_collection()
        del collection.buffer.rate_limit_hz
        self.assertEqual(collection._effective_beam_rate(), 120)

    def test_no_beam_raises(self):
        with self.assertRaises(RuntimeError):
            _make_collection(beam_rate=0)._effective_beam_rate()

    def test_timeout_uses_rate_limit(self):
        full = _make_collection()._calculate_acquisition_timeout_s()
        limited = _make_collection(
            rate_limit_hz=30.0
        )._calculate_acquisition_timeout_s()
        self.assertAlmostEqual(full, 1600 / 120 + 10.0)
        self.assertAlmostEqual(limited, 1600 / 30 * 1.25)


class ReserveBufferAreaTest(TestCase):
    @patch("slac_measurements.wires.collection.buffer.create_buffer")
    def test_area_passed_to_create_buffer(self, mock_create):
        mock_create.return_value.rate_limit_hz = 30.0
        reserve_buffer(
            "CU_HXR", pulses=350, beam_rate=120, area="LTUH", logger=MagicMock()
        )
        self.assertEqual(mock_create.call_args.kwargs["area"], "LTUH")
        self.assertEqual(mock_create.call_args.kwargs["beampath"], "CU_HXR")
