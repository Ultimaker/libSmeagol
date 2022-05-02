import json
from typing import Any, Callable, Optional

import pytest

from libSmeagol import Pocket, NonVolatilePocket


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


def _load_settings_from_pocket_file(pocket: NonVolatilePocket) -> Any:
    """Load the JSON file created by the Pocket and return the contents as a dictionary"""
    print("Loading file " + pocket.getFilename())
    with open(pocket.getFilename(), "r") as f:
        return json.load(f)


def test_save_load(pocket: NonVolatilePocket):
    """Test basic storage of Pocket data"""

    # Set up some basic keys, plus a nested SubPocket.
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("foo", "bar")
    pocket.setAsSubPocket("sub_pocket", Pocket({"my_float": 3.14, "baz": "bam"}))

    # The underlying data can be retrieved from the JSON file.
    pocket.forceSave()
    settings = _load_settings_from_pocket_file(pocket)
    assert settings == {
        "my_int": 42,
        "foo": "bar",
        "sub_pocket": {
            "my_float": 3.14,
            "baz": "bam",
        }
    }

    # We can also use a new Pocket object to retrieve the data.
    new_pocket = NonVolatilePocket(pocket.getFilename())
    assert new_pocket.get("my_int") == 42
    assert new_pocket.get("foo") == "bar"

    sub_pocket = new_pocket.getAsSubPocket("sub_pocket")
    assert isinstance(sub_pocket, Pocket)
    assert sub_pocket.getAll() == {"my_float": 3.14, "baz": "bam"}


def test_erase(pocket):
    """A NonVolatilePocket can be reset to an empty dict"""

    pocket.setAsInt("my_int", 42)
    pocket.setAsString("my_string", "FooBar")
    pocket.setAsSubPocket("sub_pocket", Pocket({"my_float": 3.14, "foo": "bar"}))
    pocket.forceSave()

    assert pocket.has("my_int")
    assert pocket.has("my_string")
    assert pocket.has("sub_pocket")

    # MISP-1812: In the original implementation of TimerPocket,
    # NonVolatilePocket.erase() would fail with a RunTimeError (because of trying
    # to start the TimerPocket's worker thread multiple times).
    pocket.erase()

    # The JSON file should be empty.
    pocket.forceSave()
    assert _load_settings_from_pocket_file(pocket) == {}

    # Pocket is empty after the reset.
    assert not pocket.has("my_int")
    assert not pocket.has("my_string")
    assert not pocket.has("sub_pocket")


def test_backup_and_setup(make_pocket):
    """A NonVolatilePocket can be reset, while preserving/forcing a subset of data"""

    pocket: NonVolatilePocket = make_pocket(save_interval=1)

    pocket.setAsInt("my_int", 42)
    pocket.setAsInt("my_int_preserved", 43)
    pocket.setAsInt("my_int_overwritten", 2)
    pocket.setAsString("my_string", "FooBar")
    pocket.setAsString("my_string_preserved", "BamBaz")
    pocket.setAsString("my_string_overwritten", "BaxBay")
    pocket.setAsSubPocket("sub_pocket", Pocket({"my_float": 3.14, "foo": "bar"}))
    pocket.forceSave()

    # We can reset a NonVolatilePocket, like with `erase()`, but...
    pocket.backupAndSetup(
        # ... preserving certain bits of data:
        keys_to_backup=["my_int_preserved", "my_string_preserved"],
        # ... and setting new bits of data to default values:
        settings_to_add={"my_int_overwritten": 10, "my_string_overwritten": "Giraffe"}
    )

    assert _load_settings_from_pocket_file(pocket) == {
        # Data that was preserved:
        "my_int_preserved": 43,
        "my_string_preserved": "BamBaz",
        # Data that was overwritten:
        "my_int_overwritten": 10,
        "my_string_overwritten": "Giraffe",
        # ...and other data was removed!
    }
