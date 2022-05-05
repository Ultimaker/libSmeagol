import json
from pathlib import Path
from time import sleep
from typing import Any, Callable, Union

import pytest

from libSmeagol import Pocket, NonVolatilePocket

DEFAULT_SAVE_INTERVAL = 2


@pytest.fixture(scope='function')
def pocket(tmp_path) -> NonVolatilePocket:
    pocket_file = tmp_path / "precious.json"
    print(f"NonVolatilePocket at {pocket_file}")
    pocket = NonVolatilePocket(str(pocket_file), save_interval=DEFAULT_SAVE_INTERVAL)
    return pocket


def _load_settings_from_pocket_file(pocket_or_path: Union[NonVolatilePocket, Path], default=None) -> Any:
    """Load the JSON file created by a Pocket and return the contents as a dictionary"""
    try:
        if isinstance(pocket_or_path, NonVolatilePocket):
            filename = Path(pocket_or_path.getFilename())
        else:
            filename = pocket_or_path
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise


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


@pytest.mark.slow
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


@pytest.mark.slow
def test_erase_timing(pocket):
    """In old libSmeagol versions, the change monitoring thread  in TimerPocket could keep running
    after a call to stop(). This could create a race condition, where the storage file on disk
    would re-appear after a call to `erase()`. This test checks specifically for that race condition.
    See https://github.com/Ultimaker/libSmeagol/commit/407a9dc8e9792a4e5cdc94b4271903797837685e
    for the commit that fixes this issue.
    """

    # We create a NonVolatilePocket that only saves data once per two seconds:
    pocket_file = Path(pocket.getFilename())

    # Set some values.
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("foo", "bar")
    pocket.setAsSubPocket("sub_pocket", Pocket({"my_float": 3.14, "bar": "baz"}))

    # Erase the Pocket; don't restart the change monitoring thread.
    sleep(2.2)
    pocket.erase(restart_after_erase=False)

    # The Pocket data file on disk should *not* come back.
    for i in range(3):
        assert not pocket_file.is_file()
        sleep(1)


@pytest.mark.slow
def test_backup_and_setup(pocket):
    """A NonVolatilePocket can be reset, while preserving/forcing a subset of data"""

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


@pytest.mark.slow
def test_erase_no_restart(pocket):
    """A NonVolatilePocket can be erased without restarting the monitor/change/save timer"""

    # Fill the Pocket with some data:
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("my_string", "FooBar")
    pocket.setAsSubPocket("sub_pocket", Pocket({"my_float": 3.14, "foo": "bar"}))

    # Wait for > 2 seconds, and the data should have been flushed to disk
    sleep(4)
    assert _load_settings_from_pocket_file(pocket) == {
        "my_int": 42,
        "my_string": "FooBar",
        "sub_pocket": {"my_float": 3.14, "foo": "bar"},
    }

    # Wipe the pocket, but do *not* restart the change monitoring thread.
    pocket.erase(restart_after_erase=False)

    # Modify the Pocket, and nothing should happen.
    pocket.setAsInt("my_int", 10)
    sub_pocket = pocket.getAsSubPocket("sub_pocket")
    sub_pocket.setAsFloat("my_float", 2.718)

    sleep(4)
    assert _load_settings_from_pocket_file(pocket, {}) == {}


@pytest.mark.slow
def test_save_rate_limit(pocket):
    """A NonVolatilePocket saves data only once per X seconds (not on every change)"""

    # Make sure the underlying JSON file has been created (just storing {} for now):
    pocket.forceSave()

    # Write some data; this should *not* be written to the file yet.
    pocket.setAsInt("my_int", 42)
    assert _load_settings_from_pocket_file(pocket) == {}
    pocket.setAsString("foo", "bar")
    assert _load_settings_from_pocket_file(pocket) == {}

    # After one more second, we should still not see any data being written.
    sleep(1)
    assert _load_settings_from_pocket_file(pocket) == {}

    # .. but the data is present in memory!
    assert pocket.getAll() == {"my_int": 42, "foo": "bar"}

    # After > 3 seconds, we should finally see that data land in the file.
    sleep(4)
    assert _load_settings_from_pocket_file(pocket) == {"my_int": 42, "foo": "bar"}

    # The file should not be modified again if the data hasn't changed.
    pocket_file = Path(pocket.getFilename())
    mtime_0 = pocket_file.stat().st_mtime
    sleep(4)
    assert pocket_file.stat().st_mtime == mtime_0


@pytest.mark.slow
def test_save_subpocket(pocket):
    """Saving a SubPocket should trigger the parent to save data to disk"""

    # Set some values.
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("foo", "bar")
    pocket.setAsSubPocket("sub_pocket", Pocket({"my_float": 3.14, "bar": "baz"}))

    # Wait until the data has been written to disk, after the "save interval".
    sleep(4)

    # Modify the SubPocket.
    # FIXME This only works if we use `getAsSubPocket` to explicitly wrap the
    #       nested dict in a new `Pocket` object. This is likely a bug.
    sub_pocket = pocket.getAsSubPocket("sub_pocket")
    sub_pocket.set("my_float", 2.718)
    assert _load_settings_from_pocket_file(pocket)["sub_pocket"]["my_float"] == 3.14

    # After waiting another save interval, the data should be written to disk.
    sleep(4)
    assert _load_settings_from_pocket_file(pocket)["sub_pocket"]["my_float"] == 2.718


def test_save_upon_exit(pocket):
    """When a Pocket gets destroyed, it should first write its data to disk"""

    # We start with an empty NonVolatilePocket that's saved to disk:
    pocket.forceSave()

    pocket_file = Path(pocket.getFilename())
    assert _load_settings_from_pocket_file(pocket_file) == {}

    # We then make some modifications:
    pocket.setAsInt("my_int", 42)
    pocket.setAsString("foo", "bar")

    # FIXME NonVolatilePocket only triggers a save using the `atexit` module. So to test that
    #       behavior, we have to reach into the innards of `atexit`. Not nice!
    #       Really, NonVolatilePocket should implement more robust cleanup behavior.
    import atexit
    atexit._run_exitfuncs()

    assert _load_settings_from_pocket_file(pocket_file) == {"my_int": 42, "foo": "bar"}


@pytest.mark.xfail
def test_save_upon_destruction(pocket):
    """When a Pocket gets destroyed, it should first write its data to disk"""

    # We start with an empty NonVolatilePocket that's saved to disk:
    pocket.forceSave()
    pocket_file = Path(pocket.getFilename())
    assert _load_settings_from_pocket_file(pocket_file) == {}

    pocket.setAsInt("my_int", 42)
    pocket.setAsString("foo", "bar")

    # Delete the Pocket: it should write the data to disk first.
    del pocket

    # FIXME ... it doesn't
    assert _load_settings_from_pocket_file(pocket_file) == {"my_int": 42, "foo": "bar"}
