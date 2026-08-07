import logging
import getpass

import numpy as np

from slac_timing import create_buffer, Buffer


_BUFFER_NAME = "SLAC Tools Wire Scan"
_MAX_BEAM_RATE = 16000
_MIN_BEAM_RATE = 10


class BufferError(Exception):
    pass


def _get_username() -> str:
    """Return the current username."""
    user = getpass.getuser()
    if user:
        return user

    raise BufferError("Could not determine current username for buffer reservation.")


def buffer_limit_for_beampath(beampath: str) -> int:
    """Return the maximum buffer points for a given beampath."""
    if beampath.startswith("CU"):
        return 2800
    return 20000


def reserve_buffer(
    beampath: str,
    pulses: int,
    beam_rate: int,
    name: str = _BUFFER_NAME,
    logger: logging.Logger | None = None,
) -> Buffer:
    user = _get_username()
    if logger:
        logger.info("Reserving buffer...")

    buf = create_buffer(
        beampath=beampath,
        n_measurements=_calculate_buffer_points(pulses, beam_rate),
        user=user,
        name=name,
    )

    if logger:
        logger.info("Reserved timing buffer %s.", buf.number)

    return buf


def _log_range():
    return np.log10(_MAX_BEAM_RATE) - np.log10(_MIN_BEAM_RATE)


def _rate_factor(rate):
    return (np.log10(rate) - np.log10(_MIN_BEAM_RATE)) / _log_range()


def _fudge(rate):
    return 1.5 - 0.4 * _rate_factor(rate)


def _calculate_buffer_points(pulses, rate) -> int:
    """
    Determine the number of buffer points for a wire scan.

    The beam rate and pulses per profile are used here to calculate the
    wire speed, which in turn defines how many BSA buffer points are needed
    to capture the full scan. The minimum safe wire speed is calculated
    separately and enforced by the motion IOC. The buffer size must be
    sufficient for data collection while staying under the 20,000-point
    operational limit.

    In the historical mode (120 Hz, 350 pulses), ~1,450 points are
    required. In the expected high-rate mode (16 kHz, 5,000 pulses), the
    function estimates ~19,166 points, still within the system limit.

    Returns
    -------
    int
        Estimated number of buffer points to allocate for the scan.
    """
    if rate is None or rate <= 0:
        raise ValueError(f"Invalid beam rate: {rate}. Must be a positive number.")

    return int(pulses * 3 * _fudge(rate) + rate / 6)


def calculate_optimal_scan_pulses(
    beam_rate: float,
    beampath: str,
    range_distance: int = 4000,
    speed_min: float = 1000.0,
    speed_max: float = 30000.0,
    target_resolution: float = 11.0,
) -> int:
    """Calculate optimal scan_pulses for a fixed scan range.

    Finds the scan_pulses value that targets `target_resolution` spatial
    resolution while respecting buffer point limits and wire speed constraints.
    At high beam rates where speed constraints force more pulses, the
    resolution will be finer than the target.

    Parameters
    ----------
    beam_rate : float
        Current beam rate in Hz.
    beampath : str
        Accelerator beampath (e.g. "CU_HXR", "SC_BSYD"). Used to determine
        the buffer point limit (2800 for CU, 20000 for SC).
    range_distance : int
        Scan range in microns. Default 4000.
    speed_min : float
        Minimum allowed wire speed in um/s. Default 1000 (administrative limit).
        If MPS speed is available and > 1000, pass that instead.
    speed_max : float
        Maximum allowed wire speed in um/s. Default 30000 (from MOTR.VMAX).
    target_resolution : float
        Target spatial resolution in um/pulse. Default 11.

    Returns
    -------
    int
        Optimal scan_pulses value.

    Raises
    ------
    ValueError
        If no valid scan_pulses satisfies all constraints simultaneously.
    """
    if beam_rate <= 0:
        raise ValueError(f"Invalid beam rate: {beam_rate}. Must be positive.")
    buffer_limit = buffer_limit_for_beampath(beampath)
    if range_distance <= 0:
        raise ValueError(f"Invalid range distance: {range_distance}. Must be positive.")
    if speed_min >= speed_max:
        raise ValueError(
            f"speed_min ({speed_min}) must be less than speed_max ({speed_max})."
        )

    target_pulses = int(np.ceil(range_distance / target_resolution))
    max_pulses_buffer = int((buffer_limit - beam_rate / 6) / (3 * _fudge(beam_rate)))
    max_pulses_speed = int((beam_rate * range_distance) / speed_min)
    min_pulses_speed = int(np.ceil((beam_rate * range_distance) / speed_max))

    upper_bound = min(target_pulses, max_pulses_buffer, max_pulses_speed)

    if min_pulses_speed > min(max_pulses_buffer, max_pulses_speed):
        raise ValueError(
            f"No valid scan_pulses exists. speed_max requires pulses >= {min_pulses_speed}, "
            f"but buffer limits pulses to {max_pulses_buffer} and "
            f"speed_min limits pulses to {max_pulses_speed}."
        )

    return max(min_pulses_speed, upper_bound)
