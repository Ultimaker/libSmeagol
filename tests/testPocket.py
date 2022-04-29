from typing import Any

import pytest

from libSmeagol import Pocket


def test_init_with_pocket():
    """We can initialize a Pocket with another Pocket, in which case it should create an
    independent deepcopy of the original"""

    orig_pocket = Pocket({"int": 101, "float": 13.501, "bool": False, "string": "test_case"})
    new_pocket = Pocket(orig_pocket)

    orig_pocket.set("int", 99)
    assert new_pocket.get("int") == 101

    new_pocket.set("string", "new_case")
    assert orig_pocket.get("string") == "test_case"


def test_unknown_key():
    """Test unknown key with default value"""
    pocket = Pocket()

    value = pocket.get("UnknownKey", "DefaultValue")
    assert value == "DefaultValue"


@pytest.mark.parametrize("name,value,expected", [
    ("int", 101, "101"),
    ("float", 13.501, "13.501"),
    ("bool", True, "True"),
    ("string", "test_case", "test_case"),
])
def test_getSetAsString(name, value, expected):
    """Test getAsString conversions"""

    # getAsString forces the set value to be read out as a string:
    pocket = Pocket()
    pocket.set(name, value)
    assert pocket.getAsString(name) == expected

    # Conversely, setAsString forces the value to be stored as a string:
    pocket = Pocket()
    pocket.setAsString(name, value)
    assert pocket.get(name) == expected


@pytest.mark.parametrize("name,value,expected", [
    ("int_zero", 0, False),
    ("int_not_zero", 1, True),
    ("int_negative", -1, True),
    ("float", 13.501, True),
    ("bool_true", True, True),
    ("bool_false", False, False),
    ("string_yes", "yes", True),
    ("string_true", "true", True),
    ("string_no", "no", False),
    ("string_false", "false", False),
    ("string_1", "1", True),
    ("string_0", "0", False),
    ("string_float_0", "0.00", False),
    ("string_float_1", "13.5e-3", True),
    ("string_float_2", "0.00e-10", False),
    ("string_float_not_zero", "13.37", True),
])
def test_setGetAsBoolean(name, value, expected):
    """Test getAsBoolean conversions"""

    # getAsBoolean forces the set  value to be read out as a boolean:
    pocket = Pocket()
    pocket.set(name, value)
    assert pocket.getAsBoolean(name) == expected

    # Conversely, setAsBoolean forces the value to be stored as a boolean:
    pocket = Pocket()
    pocket.setAsBoolean(name, value)
    assert pocket.get(name) == expected


@pytest.mark.parametrize("string_value", ["nan", "abc"])
def test_invalid_conversions(string_value):
    """
    Test some invalid type conversions: these should always fall back
    to default values
    """
    pocket = Pocket()
    pocket.setAsString("value", string_value)

    assert pocket.getAsInt("value") is None


def test_getSetAsSubPocket():
    """Test setting a dictionary value as pocket"""
    settings = {"int": 101, "float": 13.501, "bool": True, "string": "test_case"}

    pocket = Pocket()
    subpocket = Pocket(settings)
    pocket.setAsSubPocket("subpocket", subpocket)

    # After storing the subpocket, we can retrieve it
    assert pocket.get("subpocket") == settings
    assert pocket.getAsSubPocket("subpocket").getAll() == settings

    # We cannot call setAsSubPocket with anything but a Pocket
    with pytest.raises(ValueError):
        pocket.setAsSubPocket("no_pocket", 123)

    # Calling getAsSubPocket on a non-dict value gives us the default value
    assert subpocket.getAsSubPocket("int") is None


def test_getAsSubPocket_unknown_key():
    """Test getting a pocket using from an unknown key"""
    pocket = Pocket()

    # Retrieving an known subpocket gives us an empty Pocket.
    subpocket = pocket.getAsSubPocket("unknown")
    assert isinstance(subpocket, Pocket)
    assert subpocket.getAll() == {}

    # After retrieving the unknown sub-Pocket, it has magically materialized
    # in the parent Pocket. (This is bizarre behavior, but it's what's currently
    # implemented.)
    assert pocket.has("unknown")
    assert pocket.get("unknown") == {}


def test_getSetAsList():
    """Test setting a list"""
    settings = ["alpha", "bravo", "charlie"]

    # setAsList stores a copy of the list
    pocket = Pocket()
    pocket.setAsList("a_list", settings)

    a_list = pocket.get("a_list")
    assert isinstance(a_list, list)
    assert a_list == settings

    # The returned list is a copy:
    a_list.append("delta")
    assert len(pocket.get("a_list")) == 3

    # setAsList only accepts lists:
    with pytest.raises(ValueError):
        pocket.setAsList("not_a_list", 123)

    # Calling getAsList on a non-list value gives us the default value, None
    pocket.set("not_a_list", 123)
    assert pocket.getAsList("not_a_list") is None

    # Calling getAsList on an unknown key also gives us None
    assert pocket.getAsList("unknown_key") is None


def test_nested_pocket():
    """Test nested pocket"""
    # Arrange
    settings = {
        "nozzle": {
            "1": {
                "material_id": "6976d020-18d1-4d46-9f3e-411189a1e230",
                "skew": [0.0, -0.02],
                "size": 0.4
            },
            "2": {
                "material_id": "6976d020-18d1-4d46-9f3e-411189a1e230",
                "skew": [0.1, -0.01],
                "size": 0.25
            }
        }
    }
    pocket = Pocket()
    pocket.set("head", settings)

    # Get nested dicts as sub-Pocket objects:
    head = pocket.getAsSubPocket("head")
    assert head is not None

    nozzle = head.getAsSubPocket("nozzle")
    assert nozzle is not None

    # We can add values to the nested dicts:
    nozzle_1 = nozzle.getAsSubPocket("1", None)
    assert nozzle_1 is not None

    nozzle_1.setAsInt("max_temperature", 120)

    assert "max_temperature" in pocket.get("head")["nozzle"]["1"]
    assert pocket.get("head")["nozzle"]["1"]["max_temperature"] == 120

    # We can modify values in the nested dicts:
    nozzle_2 = nozzle.getAsSubPocket("2", None)
    assert nozzle_2 is not None

    nozzle_2.setAsFloat("size", 0.4)

    assert pocket.get("head")["nozzle"]["2"]["size"] == 0.4

    # We can automagically create new subpockets by requesting acccess to them:
    nozzle_3 = nozzle.getAsSubPocket("3")
    assert nozzle_3 is not None

    nozzle_3.setAsFloat("new_data", 0.4)

    assert pocket.get("head")["nozzle"]["3"]["new_data"] == 0.4
