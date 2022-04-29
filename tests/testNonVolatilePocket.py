import json
from typing import Any, Callable, Optional

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


def test_save_preference(pocket: NonVolatilePocket):
    """Simple set value / wait for save / verify save test (implies get/set test)"""
    # Arrange
    key = "TestKey"
    value = "dummy_value"

    # Act
    pocket.setAsString(key, value)
    pocket.forceSave()
    settings = _load_settings_from_pocket_file(pocket)

    # Assert
    assert value == settings[key]


def _load_settings_from_pocket_file(pocket: NonVolatilePocket) -> Any:
    """Load the JSON file created by the Pocket and return the contents as a dictionary"""
    print("Loading file " + pocket.getFilename())
    with open(pocket.getFilename(), "r") as f:
        return json.load(f)


def test_erase(make_pocket):
    pocket = make_pocket()
    print(f'@@ {pocket.getFilename()}')
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("my_string", "FooBar")
    pocket.forceSave()

    # MISP-1812: In the original implementation of TimerPocket,
    # NonVolatilePocket.erase() would fail with a RunTimeError (because of trying
    # to start the TimerPocket's worker thread multiple times).
    pocket.erase()


def test_backup_and_setup(make_pocket):
    pocket = make_pocket(save_interval=1)
    print(f'@@ {pocket.getFilename()}')
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("my_string", "FooBar")
