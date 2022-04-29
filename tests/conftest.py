# Pytest fixtures shared across all tests.

from typing import Callable

import pytest

from libSmeagol import NonVolatilePocket


DEFAULT_SAVE_INTERVAL = 2


@pytest.fixture()
def make_pocket(tmp_path_factory: pytest.TempPathFactory) -> Callable[[], NonVolatilePocket]:
    """Fixture for creating a new NonVolatilePocket, backed by a new temp file"""

    def _make_pocket(save_interval: int = DEFAULT_SAVE_INTERVAL) -> NonVolatilePocket:
        """Make a NonVolatilePocket, backed by a fresh temp file

        Args:
            save_interval: see NonVolatilePocket()
        """
        pocket_file = tmp_path_factory.mktemp('nvp') / "testpocket.json"
        print(f"NonVolatilePocket at {pocket_file}")
        pocket = NonVolatilePocket(str(pocket_file), save_interval=save_interval)
        return pocket

    return _make_pocket


@pytest.fixture(scope='function')
def pocket(make_pocket) -> NonVolatilePocket:
    return make_pocket()
