from __future__ import annotations

from typing import NamedTuple


def resolve_timing_key(beampath: str) -> str:
    """Derive the CU/SC timing key from a beampath string."""
    return "CU" if beampath.startswith("CU") else "SC"


def pick_by_timing(
    detector_container: str | list[str] | dict[str, str] | dict[str, list[str]],
    beampath: str,
    fallback: str | list[str] | None = None,
) -> str | list[str] | None:
    """If *detector_container* is a dict keyed by CU/SC, return the entry for the active timing; otherwise pass through."""
    if isinstance(detector_container, dict):
        timing = resolve_timing_key(beampath)
        return detector_container.get(timing, fallback)
    return detector_container


def strip_colon_suffix(name: str) -> str:
    """Remove the ':area' suffix from a device-layer detector string.

    ``"PMT756:LTUH"`` becomes ``"PMT756"``.
    """
    return name.split(":", 1)[0]


def split_detector_string(detector_string: str) -> tuple[str, str]:
    """Split a device-layer detector string into ``(name, area)``.

    ``"PMT756:LTUH"`` becomes ``("PMT756", "LTUH")``.
    """
    name, area = detector_string.split(":", 1)
    return name, area


class DetectorConfig(NamedTuple):
    """Result of resolving Wire metadata detectors for a beampath."""

    names: list[str]
    default: str
    raw_strings: list[str]


def resolve_detectors(
    detectors: list[str] | dict[str, list[str]],
    default_detector: str | dict[str, str],
    beampath: str,
) -> DetectorConfig:
    """Resolve detector timing dicts, strip colon suffixes, and determine
    the default detector for a given beampath.

    Parameters
    ----------
    detectors
        Detector list from Wire metadata (flat or timing-keyed).
    default_detector
        Default detector from Wire metadata (plain or timing-keyed).
    beampath
        Active beampath string (e.g. ``"CU_HXR"``).

    Returns
    -------
    DetectorConfig
        ``names`` — colon-stripped detector names.
        ``default`` — colon-stripped default detector name.
        ``raw_strings`` — original timing-resolved strings with colon
        suffixes intact (needed for device instantiation).
    """
    timing = resolve_timing_key(beampath)

    if isinstance(detectors, dict):
        raw_strings = detectors.get(timing, [])
    else:
        raw_strings = detectors

    if isinstance(default_detector, dict):
        raw_default = default_detector.get(timing, "")
    else:
        raw_default = default_detector

    names = [strip_colon_suffix(d) for d in raw_strings]

    if raw_default:
        default = strip_colon_suffix(raw_default)
    elif names:
        default = names[0]
    else:
        raise RuntimeError("No detectors available; cannot determine default detector.")

    return DetectorConfig(names=names, default=default, raw_strings=raw_strings)
