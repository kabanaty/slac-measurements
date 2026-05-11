import numpy as np
from slac_devices.reader import create_beampath
from slac_devices.wire import Wire
from slac_measurements.measurement import Measurement
from slac_measurements.utils import collect_with_size_check
from edef import BSABuffer, EventDefinition
from pydantic import model_validator
from typing import Optional


class TMITLoss(Measurement):
    """Measures percentage beam intensity loss across a wire scanner."""

    name: str = "TMIT Loss"
    buffer: BSABuffer | EventDefinition
    beampath: str
    beam_profile_device: Wire

    idx_upstream: Optional[list] = None
    idx_downstream: Optional[list] = None
    bpms: Optional[dict] = None

    @model_validator(mode="after")
    def run_setup(self) -> "TMITLoss":
        """Load BPMs from beampath and resolve before/after wire indices."""

        def _build_bpm_lookup() -> dict:
            """Instantiate all BPMs in the beampath, sorted by z-position."""
            beampath_obj = create_beampath(self.beampath)
            all_bpms = beampath_obj.bpms
            if not all_bpms:
                raise LookupError("No BPMs found in beampath.")
            return dict(sorted(all_bpms.items(), key=lambda item: item[1].z_location))

        def _resolve_wire_bpms() -> tuple:
            """Map wire metadata BPM names to row indices in the data array."""
            bpms_upstream = self.beam_profile_device.metadata.tmitloss.upstream
            bpms_downstream = self.beam_profile_device.metadata.tmitloss.downstream

            bpm_names = list(self.bpms.keys())
            idx_upstream = [
                bpm_names.index(name) for name in bpms_upstream if name in self.bpms
            ]
            idx_downstream = [
                bpm_names.index(name) for name in bpms_downstream if name in self.bpms
            ]

            return idx_upstream, idx_downstream

        self.bpms = _build_bpm_lookup()
        self.idx_upstream, self.idx_downstream = _resolve_wire_bpms()
        return self

    def measure(self):
        """Acquire TMIT data and return percentage loss as a numpy array."""
        data = self.get_bpm_data()
        return self.calc_tmit_loss(data)

    def get_bpm_data(self) -> np.ndarray:
        """Collect TMIT buffer data from all BPMs. Returns shape (n_bpms, n_samples)."""
        rows = []
        n_samples = self.buffer.n_measurements
        for name, bpm in self.bpms.items():
            try:
                bpm_data = collect_with_size_check(
                    bpm, "tmit_buffer", self.buffer, None
                )
            except (TypeError, BufferError) as e:
                print(f"Skipping BPM {name}: {e}")
                bpm_data = np.full(n_samples, np.nan)
            rows.append(bpm_data)
        return np.array(rows)

    def calc_tmit_loss(self, data: np.ndarray) -> np.ndarray:
        """Normalize TMIT data and compute percentage loss between before/after wire BPMs."""
        row_medians = np.nanmedian(data, axis=1, keepdims=True)
        ironed = data / row_medians

        mean_iron_upstream = np.nanmean(ironed[self.idx_upstream], axis=0)
        normed = ironed / mean_iron_upstream

        mean_upstream = np.nanmean(normed[self.idx_upstream], axis=0)
        mean_downstream = np.nanmean(normed[self.idx_downstream], axis=0)

        return (mean_upstream - mean_downstream) * 100
