import time

from slac_measurements.wires.collection import BaseWireMeasurementCollection


class OTFWireMeasurementCollection(BaseWireMeasurementCollection):
    """Collect wire scan data using on-the-fly wire motion."""

    def _run_collection_scan(self) -> None:
        self._initialize_wire_with_retry(scan_mode="otf")
        self._start_timing_buffer()

    def _start_timing_buffer(self) -> None:
        """Start BSA buffer and wait for completion while logging wire position."""
        self.logger.info("Starting BSA buffer...")
        self.my_buffer.start()

        time.sleep(0.5)

        i = 0
        while not self.my_buffer.is_acquisition_complete():
            time.sleep(0.1)
            if i % 10 == 0:
                self.logger.info("Wire position: %s", self.my_wire.motor_rbv)
            i += 1

        self.logger.info(
            "BSA buffer %s acquisition complete after %s seconds",
            self.my_buffer.number,
            i / 10,
        )
