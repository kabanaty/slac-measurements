from types import SimpleNamespace

from slac_measurements.wires.collection.base import _resolve_detectors


def _make_metadata(detectors, default_detector):
    return SimpleNamespace(detectors=detectors, default_detector=default_detector)


class TestResolveDetectors:
    def test_flat_list_passthrough(self):
        meta = _make_metadata(
            detectors=["PMT122:LTUH", "LBLM32A:LTUH"],
            default_detector="PMT122:LTUH",
        )
        dets, default = _resolve_detectors(meta, "CU_HXR")
        assert dets == ["PMT122:LTUH", "LBLM32A:LTUH"]
        assert default == "PMT122:LTUH"

    def test_dict_cu_beampath(self):
        meta = _make_metadata(
            detectors={
                "CU": ["PMT122:LTUH", "LBLM32A:LTUH"],
                "SC": ["LBLM32A:LTUH"],
            },
            default_detector={"CU": "PMT122:LTUH", "SC": "LBLM32A:LTUH"},
        )
        dets, default = _resolve_detectors(meta, "CU_HXR")
        assert dets == ["PMT122:LTUH", "LBLM32A:LTUH"]
        assert default == "PMT122:LTUH"

    def test_dict_sc_beampath(self):
        meta = _make_metadata(
            detectors={
                "CU": ["PMT122:LTUH", "LBLM32A:LTUH"],
                "SC": ["LBLM32A:LTUH"],
            },
            default_detector={"CU": "PMT122:LTUH", "SC": "LBLM32A:LTUH"},
        )
        dets, default = _resolve_detectors(meta, "SC_HXR")
        assert dets == ["LBLM32A:LTUH"]
        assert default == "LBLM32A:LTUH"

    def test_dict_sc_sxr_beampath(self):
        meta = _make_metadata(
            detectors={
                "CU": ["LBLMS32A:LTUS"],
                "SC": ["LBLMS32A:LTUS", "TMITLOSS:LTUS"],
            },
            default_detector={"CU": "LBLMS32A:LTUS", "SC": "TMITLOSS:LTUS"},
        )
        dets, default = _resolve_detectors(meta, "SC_SXR")
        assert dets == ["LBLMS32A:LTUS", "TMITLOSS:LTUS"]
        assert default == "TMITLOSS:LTUS"

    def test_dict_missing_key_returns_empty(self):
        meta = _make_metadata(
            detectors={"SC": ["LBLM32A:LTUH"]},
            default_detector={"SC": "LBLM32A:LTUH"},
        )
        dets, default = _resolve_detectors(meta, "CU_HXR")
        assert dets == []
        assert default == ""
