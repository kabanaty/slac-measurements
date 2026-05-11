import gc

import numpy as np
from slac_devices.reader import create_beampath
from slac_devices.wire import Wire
from slac_measurements.measurement import Measurement
from slac_measurements.utils import collect_with_size_check
from edef import BSABuffer, EventDefinition


class TMITLoss(Measurement):
    """Measures percentage beam intensity loss across a wire scanner."""

    name: str = "TMIT Loss"
    buffer: BSABuffer | EventDefinition
    beampath: str
    beam_profile_device: Wire

    def measure(self):
        """Acquire TMIT data and return percentage loss as a numpy array."""
        bpms, idx_upstream, idx_downstream = self._build_bpm_state()
        try:
            data = self._get_bpm_data(bpms)
            return self._calc_tmit_loss(data, idx_upstream, idx_downstream)
        finally:
            del bpms
            gc.collect()

    def _build_bpm_state(self) -> tuple:
        """Instantiate BPMs from beampath and resolve upstream/downstream indices."""
        beampath_obj = create_beampath(self.beampath)
        all_bpms = beampath_obj.bpms
        if not all_bpms:
            raise LookupError("No BPMs found in beampath.")
        bpms = dict(sorted(all_bpms.items(), key=lambda item: item[1].z_location))

        bpms_upstream = self.beam_profile_device.metadata.tmitloss.upstream
        bpms_downstream = self.beam_profile_device.metadata.tmitloss.downstream
        bpm_names = list(bpms.keys())
        idx_upstream = [bpm_names.index(name) for name in bpms_upstream if name in bpms]
        idx_downstream = [
            bpm_names.index(name) for name in bpms_downstream if name in bpms
        ]

        return bpms, idx_upstream, idx_downstream

    def _get_bpm_data(self, bpms: dict) -> np.ndarray:
        """Collect TMIT buffer data from all BPMs. Returns shape (n_bpms, n_samples)."""
        rows = []
        n_samples = self.buffer.n_measurements
        for name, bpm in bpms.items():
            try:
                bpm_data = collect_with_size_check(
                    bpm, "tmit_buffer", self.buffer, None
                )
            except (TypeError, BufferError) as e:
                print(f"Skipping BPM {name}: {e}")
                bpm_data = np.full(n_samples, np.nan)
            rows.append(bpm_data)
        return np.array(rows)

    @staticmethod
    def _calc_tmit_loss(
        data: np.ndarray, idx_upstream: list, idx_downstream: list
    ) -> np.ndarray:
        """Normalize TMIT data and compute percentage loss between before/after wire BPMs."""
        row_medians = np.nanmedian(data, axis=1, keepdims=True)
        ironed = data / row_medians

        mean_iron_upstream = np.nanmean(ironed[idx_upstream], axis=0)
        normed = ironed / mean_iron_upstream

        mean_upstream = np.nanmean(normed[idx_upstream], axis=0)
        mean_downstream = np.nanmean(normed[idx_downstream], axis=0)

        return (mean_upstream - mean_downstream) * 100
