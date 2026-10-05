import functools
import sys
from types import ModuleType
from unittest.mock import MagicMock

_meme = ModuleType("meme")
_meme_model = ModuleType("meme.model")
_meme_model.Model = MagicMock()
_meme.model = _meme_model


def mock_meme(test_func):
    """Decorator: registers a fake meme/meme.model module before the test
    runs, so a @patch("meme.model.Model") stacked below this can resolve
    it -- meme is an optional dependency not installed in CI."""

    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        sys.modules.setdefault("meme", _meme)
        sys.modules.setdefault("meme.model", _meme_model)
        return test_func(*args, **kwargs)

    return wrapper
