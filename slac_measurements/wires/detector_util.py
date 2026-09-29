def resolve_timing_key(beampath: str) -> str:
    """Derive the CU/SC timing key from a beampath string."""
    return "CU" if beampath.startswith("CU") else "SC"


def pick_by_timing(value, beampath: str, fallback=None):
    """If *value* is a dict keyed by CU/SC, return the entry for the active timing; otherwise pass through."""
    if isinstance(value, dict):
        timing = resolve_timing_key(beampath)
        return value.get(timing, fallback)
    return value
