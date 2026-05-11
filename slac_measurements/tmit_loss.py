import numpy as np
from slac_devices.reader import create_beampath
from slac_devices.wire import Wire
from slac_measurements.measurement import Measurement
from slac_measurements.utils import collect_with_size_check
from edef import BSABuffer
from pydantic import model_validator
from typing import Optional


class TMITLoss(Measurement):
    name: str = "TMIT Loss"
    buffer: BSABuffer
    beampath: str
    region: str
    beam_profile_device: Wire

    idx_before: Optional[list] = None
    idx_after: Optional[list] = None
    bpms: Optional[dict] = None

    @model_validator(mode="after")
    def run_setup(self) -> "TMITLoss":
        def _build_bpm_lookup() -> dict:
            beampath_obj = create_beampath(self.beampath)
            all_bpms = beampath_obj.bpms
            if not all_bpms:
                raise LookupError("No BPMs found in beampath.")
            return dict(sorted(all_bpms.items(), key=lambda item: item[1].z_location))

        def _resolve_wire_bpms() -> tuple:
            tmit_regions = {
                "HTR",
                "DIAG0",
                "COL1",
                "EMIT2",
                "DOG",
                "BYP",
                "SPD",
                "LTUS",
            }
            if self.region not in tmit_regions:
                valid_regions_str = ", ".join(sorted(tmit_regions))
                raise ValueError(
                    f"Invalid region '{self.region}'. Must be one of {valid_regions_str}."
                )

            bpms_before = self.beam_profile_device.metadata.bpms_before_wire
            bpms_after = self.beam_profile_device.metadata.bpms_after_wire

            bpm_names = list(self.bpms.keys())
            idx_before = [
                bpm_names.index(name) for name in bpms_before if name in self.bpms
            ]
            idx_after = [
                bpm_names.index(name) for name in bpms_after if name in self.bpms
            ]

            return idx_before, idx_after

        self.bpms = _build_bpm_lookup()
        self.idx_before, self.idx_after = _resolve_wire_bpms()
        return self

    def measure(self):
        data = self.get_bpm_data()
        return self.calc_tmit_loss(data)

    def get_bpm_data(self) -> np.ndarray:
        rows = []
        for bpm in self.bpms.values():
            bpm_data = collect_with_size_check(bpm, "tmit_buffer", self.buffer, None)
            rows.append(bpm_data)
        return np.array(rows)

    def calc_tmit_loss(self, data: np.ndarray) -> np.ndarray:
        row_medians = np.median(data, axis=1, keepdims=True)
        ironed = data / row_medians

        mean_iron_before = ironed[self.idx_before].mean(axis=0)
        normed = ironed / mean_iron_before

        mean_before = normed[self.idx_before].mean(axis=0)
        mean_after = normed[self.idx_after].mean(axis=0)

        return (mean_before - mean_after) * 100
