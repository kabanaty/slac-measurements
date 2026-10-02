import pytest
from slac_measurements.wires.detector_util import (
    resolve_beampath_key,
    pick_by_beampath,
    strip_colon_suffix,
    resolve_detectors,
)


class TestResolveBeampathKey:
    def test_cu_beampath(self):
        assert resolve_beampath_key("CU_HXR") == "CU"

    def test_sc_beampath(self):
        assert resolve_beampath_key("SC_SXR") == "SC"

    def test_cu_prefix_only(self):
        assert resolve_beampath_key("CU") == "CU"


class TestPickByBeampath:
    def test_dict_cu(self):
        assert pick_by_beampath({"CU": "PMT756", "SC": "LBLM32A"}, "CU_HXR") == "PMT756"

    def test_dict_sc(self):
        assert (
            pick_by_beampath({"CU": "PMT756", "SC": "LBLM32A"}, "SC_HXR") == "LBLM32A"
        )

    def test_dict_missing_key_returns_fallback(self):
        assert pick_by_beampath({"SC": "LBLM32A"}, "CU_HXR", fallback="") == ""

    def test_dict_missing_key_default_fallback_is_none(self):
        assert pick_by_beampath({"SC": "LBLM32A"}, "CU_HXR") is None

    def test_flat_string_passthrough(self):
        assert pick_by_beampath("PMT756:LTUH", "CU_HXR") == "PMT756:LTUH"

    def test_flat_list_passthrough(self):
        detectors = ["PMT122:LTUH", "LBLM32A:LTUH"]
        assert pick_by_beampath(detectors, "SC_HXR") == detectors


class TestStripColonSuffix:
    def test_strips_colon(self):
        assert strip_colon_suffix("PMT756:LTUH") == "PMT756"

    def test_no_colon_passthrough(self):
        assert strip_colon_suffix("PMT756") == "PMT756"

    def test_empty_string(self):
        assert strip_colon_suffix("") == ""

    def test_multiple_colons_strips_first(self):
        assert strip_colon_suffix("PMT:LI28:extra") == "PMT"


class TestResolveDetectors:
    def test_flat_list_passthrough(self):
        config = resolve_detectors(
            detectors=["PMT122:LTUH", "LBLM32A:LTUH"],
            default_detector="PMT122:LTUH",
            beampath="CU_HXR",
        )
        assert config.names == ["PMT122", "LBLM32A"]
        assert config.default == "PMT122"
        assert config.raw_strings == ["PMT122:LTUH", "LBLM32A:LTUH"]

    def test_dict_cu_beampath(self):
        config = resolve_detectors(
            detectors={
                "CU": ["PMT122:LTUH", "LBLM32A:LTUH"],
                "SC": ["LBLM32A:LTUH"],
            },
            default_detector={"CU": "PMT122:LTUH", "SC": "LBLM32A:LTUH"},
            beampath="CU_HXR",
        )
        assert config.names == ["PMT122", "LBLM32A"]
        assert config.default == "PMT122"
        assert config.raw_strings == ["PMT122:LTUH", "LBLM32A:LTUH"]

    def test_dict_sc_beampath(self):
        config = resolve_detectors(
            detectors={
                "CU": ["PMT122:LTUH", "LBLM32A:LTUH"],
                "SC": ["LBLM32A:LTUH"],
            },
            default_detector={"CU": "PMT122:LTUH", "SC": "LBLM32A:LTUH"},
            beampath="SC_HXR",
        )
        assert config.names == ["LBLM32A"]
        assert config.default == "LBLM32A"
        assert config.raw_strings == ["LBLM32A:LTUH"]

    def test_dict_sc_sxr_beampath(self):
        config = resolve_detectors(
            detectors={
                "CU": ["LBLMS32A:LTUS"],
                "SC": ["LBLMS32A:LTUS", "TMITLOSS:LTUS"],
            },
            default_detector={"CU": "LBLMS32A:LTUS", "SC": "TMITLOSS:LTUS"},
            beampath="SC_SXR",
        )
        assert config.names == ["LBLMS32A", "TMITLOSS"]
        assert config.default == "TMITLOSS"
        assert config.raw_strings == ["LBLMS32A:LTUS", "TMITLOSS:LTUS"]

    def test_empty_default_falls_back_to_first_detector(self):
        config = resolve_detectors(
            detectors=["PMT756:LTUH"],
            default_detector="",
            beampath="CU_HXR",
        )
        assert config.default == "PMT756"

    def test_dict_missing_key_falls_back_to_first_detector(self):
        config = resolve_detectors(
            detectors=["PMT756:LTUH"],
            default_detector={"SC": "LBLM32A:LTUH"},
            beampath="CU_HXR",
        )
        assert config.default == "PMT756"

    def test_no_detectors_and_no_default_raises(self):
        with pytest.raises(RuntimeError, match="No detectors available"):
            resolve_detectors(
                detectors={"SC": ["LBLM32A:LTUH"]},
                default_detector={"SC": "LBLM32A:LTUH"},
                beampath="CU_HXR",
            )

    def test_detectors_without_colons(self):
        config = resolve_detectors(
            detectors=["PMT756", "LBLM32A"],
            default_detector="PMT756",
            beampath="CU_HXR",
        )
        assert config.names == ["PMT756", "LBLM32A"]
        assert config.default == "PMT756"
        assert config.raw_strings == ["PMT756", "LBLM32A"]
