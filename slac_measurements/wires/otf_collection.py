import logging
import time

import slac_measurements.utils

from slac_measurements.wires.collection import BaseWireMeasurementCollection

logger = logging.getLogger(__name__)


def initialize_otf_with_retry(device, logger=logger, max_attempts=3):
    """Start OTF scan and retry until wire is homed and on status.

    start_scan must always be called to arm the wire for OTF motion,
    even if homed/on_status are already True from a prior run.
    """
    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Starting OTF scan on %s (Attempt %s/%s)...",
            device.name,
            attempt,
            max_attempts,
        )
        device.start_scan()

        if slac_measurements.utils.wait_until(
            lambda: device.homed and device.on_status
        ):
            logger.info("%s is homed and on.", device.name)
            return

        logger.warning(
            "%s did not become homed and on - retrying...",
            device.name,
        )

    raise RuntimeError(
        f"Failed to initialize {device.name} after {max_attempts} attempts."
    )


class OTFWireMeasurementCollection(BaseWireMeasurementCollection):
    """Collect wire scan data using on-the-fly wire motion."""

    def _initialize_otf_with_retry(self, max_attempts: int = 3) -> None:
        initialize_otf_with_retry(self.beam_profile_device, self.logger, max_attempts)

    def _run_collection_scan(self) -> None:
        """Run an OTF scan: init wire, start buffer."""

        def _start_timing_buffer() -> None:
            """Start BSA buffer and wait for completion while logging wire position."""

            self.logger.info("Starting buffer acquisition for on-the-fly scan...")
            acquisition_start = time.monotonic()
            acquisition_timeout_s = self._calculate_acquisition_timeout_s()
            self.buffer.start()

            time.sleep(0.5)

            i = 0
            while not self.buffer.is_complete():
                elapsed_s = time.monotonic() - acquisition_start
                if elapsed_s > acquisition_timeout_s:
                    raise TimeoutError(
                        f"Timing buffer {self.buffer.number} did not complete after "
                        f"{elapsed_s:.1f}s (timeout={acquisition_timeout_s:.1f}s)."
                    )
                time.sleep(0.1)
                if i % 10 == 0:
                    wire_position = self.beam_profile_device.motor_rbv
                    self.logger.info("Wire position: %s", wire_position)
                i += 1

            self.logger.info(
                "Timing buffer %s acquisition complete after %.1f seconds",
                self.buffer.number,
                time.monotonic() - acquisition_start,
            )

        self.logger.info("Performing on-the-fly scan mode")
        self._initialize_otf_with_retry()
        _start_timing_buffer()
