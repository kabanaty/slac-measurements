from slac_measurements.wires.detector_util import resolve_timing_key, pick_by_timing
from slac_measurements.wires.analysis.analysis import _resolve_detector


class TestResolveTimingKey:
    def test_cu_beampath(self):
        assert resolve_timing_key("CU_HXR") == "CU"

    def test_sc_beampath(self):
        assert resolve_timing_key("SC_SXR") == "SC"

    def test_cu_prefix_only(self):
        assert resolve_timing_key("CU") == "CU"


class TestPickByTiming:
    def test_dict_cu(self):
        assert pick_by_timing({"CU": "PMT756", "SC": "LBLM32A"}, "CU_HXR") == "PMT756"

    def test_dict_sc(self):
        assert pick_by_timing({"CU": "PMT756", "SC": "LBLM32A"}, "SC_HXR") == "LBLM32A"

    def test_dict_missing_key_returns_fallback(self):
        assert pick_by_timing({"SC": "LBLM32A"}, "CU_HXR", fallback="") == ""

    def test_dict_missing_key_default_fallback_is_none(self):
        assert pick_by_timing({"SC": "LBLM32A"}, "CU_HXR") is None

    def test_flat_string_passthrough(self):
        assert pick_by_timing("PMT756:LTUH", "CU_HXR") == "PMT756:LTUH"

    def test_flat_list_passthrough(self):
        detectors = ["PMT122:LTUH", "LBLM32A:LTUH"]
        assert pick_by_timing(detectors, "SC_HXR") == detectors


class TestResolveDetector:
    def test_none_returns_none(self):
        assert _resolve_detector(None, "CU_HXR") is None

    def test_plain_string_passthrough(self):
        assert _resolve_detector("PMT756", "CU_HXR") == "PMT756"

    def test_strips_colon_suffix(self):
        assert _resolve_detector("PMT756:LTUH", "CU_HXR") == "PMT756"

    def test_dict_cu_beampath(self):
        det = {"CU": "PMT756:LTUH", "SC": "LBLM32A:LTUH"}
        assert _resolve_detector(det, "CU_HXR") == "PMT756"

    def test_dict_sc_beampath(self):
        det = {"CU": "PMT756:LTUH", "SC": "LBLM32A:LTUH"}
        assert _resolve_detector(det, "SC_SXR") == "LBLM32A"

    def test_dict_missing_key_returns_none(self):
        det = {"SC": "LBLM32A:LTUH"}
        assert _resolve_detector(det, "CU_HXR") is None

    def test_empty_string_returns_none(self):
        assert _resolve_detector("", "CU_HXR") is None
