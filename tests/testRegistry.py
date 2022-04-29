import json
import time

from typing import Any

import pytest

from libSmeagol import NonVolatilePocket, Pocket


def _load_settings_from_pocket_file(pocket: NonVolatilePocket) -> Any:
    """Load the JSON file created by the Pocket and return the contents as a dictionary"""
    print("Loading file " + pocket.getFilename())
    with open(pocket.getFilename(), "r") as f:
        return json.load(f)


def _update_pocket(pocket: Pocket, settings: dict) -> None:
    """
    Add settings to the pocket

    :param pocket: Pocket to update.
    :param settings: A dictionary of settings
    """
    #  @param
    for key, value in settings.items():
        pocket.set(key, value)


def test_save_preference(pocket: NonVolatilePocket):
    """Simple set value / wait for save / verify save test (implies get/set test)"""
    # Arrange
    key = "TestKey"
    value = "dummy_value"

    # Act
    pocket.setAsString(key, value)
    time.sleep(4)
    settings = _load_settings_from_pocket_file(pocket)

    # Assert
    assert value == settings[key]


def test_unknown_key(pocket: NonVolatilePocket):
    """Test unknown key with default value"""
    # Arrange
    key = "KeyDoesNotExist"
    default_value = "the_default_value"

    # Act
    value = pocket.get(key, default_value)

    # Assert
    assert value == default_value


def test_getAsString(pocket: NonVolatilePocket):
    """Test getAsString conversions"""
    # Arrange
    settings = {"int": 101, "float": 13.501, "bool": True, "string": "test_case"}
    expected = {"int": "101", "float": "13.501", "bool": "True", "string": "test_case"}

    # Act
    _update_pocket(pocket, settings)

    # Assert
    for key, value in expected.items():
        actual_value = pocket.getAsString(key)
        assert value == actual_value


def test_setAsString(pocket: NonVolatilePocket):
    """Test setAsString conversions"""
    # Arrange
    settings = {"int": 101, "float": 13.501, "bool": True, "string": "test_case"}
    expected = {"int": "101", "float": "13.501", "bool": "True", "string": "test_case"}

    # Act
    for key, value in settings.items():
        pocket.setAsString(key, value)

    # Assert
    for key, value in expected.items():
        actual_value = pocket.get(key)
        assert value == actual_value


def test_getAsBoolean(pocket: NonVolatilePocket):
    """Test getAsBoolean conversions"""
    # Arrange
    settings = {"int_zero": 0, "int_not_zero": 1, "int_positive": 1, "float": 13.501, "bool_true": True, "bool_false": False, "string_yes": "yes", "string_true": "true", "string_no": "no", "string_false": "false", "string_1": "1", "string_0": "0", "float_0": "0.00", "float_not_zero": "13.37"}
    expected = {"int_zero": False, "int_not_zero": True, "int_positive": True, "float": True, "bool_true": True, "bool_false": False, "string_yes": True, "string_true": True, "string_no": False, "string_false": False, "string_1": True, "string_0": False, "float_0": False, "float_not_zero": True}

    # Act
    _update_pocket(pocket, settings)

    # Assert
    for key, value in expected.items():
        actual_value = pocket.getAsBoolean(key)
        assert value == actual_value


def test_setAsBoolean(pocket: NonVolatilePocket):
    """Test setAsBoolean conversions"""
    # Arrange
    settings = {"int_zero": 0, "int_not_zero": 1, "int_positive": 1, "float": 13.501, "bool_true": True, "bool_false": False, "string_yes": "yes", "string_true": "true", "string_no": "no", "string_false": "false", "string_1": "1", "string_0": "0", "float_0": "0.00", "float_not_zero": "13.37"}
    expected = {"int_zero": False, "int_not_zero": True, "int_positive": True, "float": True, "bool_true": True, "bool_false": False, "string_yes": True, "string_true": True, "string_no": False, "string_false": False, "string_1": True, "string_0": False, "float_0": False, "float_not_zero": True}

    # Act
    for key, value in settings.items():
        pocket.setAsBoolean(key, value)

    # Assert
    for key, value in expected.items():
        actual_value = pocket.get(key)
        assert value == actual_value


def test_unable_conversions(pocket: NonVolatilePocket):
    """Test some unable conversions (from string to int and vv)"""
    # Arrange
    settings = {"not_a_number": "nan", "not_numeric": "abc"}
    expected = {"not_a_number": None, "not_numeric": None}

    # Act
    for key, value in settings.items():
        pocket.setAsString(key, value)

    # Assert
    for key, value in expected.items():
        actual_value = pocket.getAsInt(key)
        assert value == actual_value


def test_setAsPocket():
    """Test setting a dictionary value as pocket"""
    # Arrange
    settings = {"int": 101, "float": 13.501, "bool": True, "string": "test_case"}
    key = "test_reg"

    # Act
    pocket = Pocket()
    sub_pocket = Pocket(settings)
    pocket.setAsSubPocket(key, sub_pocket)

    # Assert
    expected = pocket.get(key)
    assert expected == settings


def test_getAsPocket():
    """Test getting a pocket value"""
    # Arrange
    settings = {"int": 101, "float": 13.501, "bool": True, "string": "test_case"}
    key = "test_reg"

    # Act
    pocket = Pocket()
    pocket.set(key, settings)

    # Assert
    sub_pocket = pocket.getAsSubPocket(key)
    assert sub_pocket.getAll() == settings


def test_set_boolean_as_pocket():
    """Test setting a pocket using a boolean value"""
    pocket = Pocket()

    with pytest.raises(ValueError):
        pocket.setAsSubPocket(key="test_set_boolean_pocket", value=True)


def test_getAsSubPocket_from_boolean():
    """Test getting a pocket using from a boolean value"""
    # Arrange
    setting = True
    key = "test_get_boolean_pocket"
    expected = None

    # Act
    pocket = Pocket()
    pocket.set(key, setting)

    # Assert
    value = pocket.getAsSubPocket(key)
    assert expected == value


def test_geeting_pocket_from_unknown_key():
    """Test getting a pocket using from an unknown key"""
    # Arrange
    key = "test_bogus_pocket"
    expected = {}

    # Act
    pocket = Pocket()
    value = pocket.getAsSubPocket(key)

    # Assert
    assert isinstance(value, Pocket)
    assert expected == value.getAll()


def test_setAsList(pocket: NonVolatilePocket):
    """Test setting a list"""
    # Arrange
    settings = ["aap", "noot", "mies"]
    key = "list_set_key"

    # Act
    pocket.setAsList(key, settings)

    # Assert
    value = pocket.get(key)
    assert isinstance(value, list)
    assert settings == value


def test_getAsList(pocket: NonVolatilePocket):
    """Test getting a list"""
    # Arrange
    settings = [ "aap", "noot", "mies" ]
    key = "list_get_key"

    # Act
    pocket.set(key, settings)

    # Assert
    value = pocket.getAsList(key)
    assert isinstance(value, list)
    assert settings == value


def test_set_boolean_as_list():
    """Test setting a list using a boolean value"""
    pocket = Pocket()

    with pytest.raises(ValueError):
        pocket.setAsList(key="test_set_boolean_list", value=True)


def test_getAsList_from_boolean():
    """Test get list from a boolean"""
    setting = True
    key = "test_get_boolean_list"

    pocket = Pocket()
    pocket.set(key, setting)

    value = pocket.getAsList(key)
    assert value is None


def test_getting_list_from_unknown_key():
    """Test getting a list using from an unknown key"""
    # Arrange
    key = "test_bogus_list"
    expected = None

    # Act
    pocket = Pocket()
    value = pocket.getAsList(key)

    # Assert
    assert expected == value


def testNestedPocket(pocket: NonVolatilePocket):
    """Test nested pocket"""
    # Arrange
    settings = {
        "nozzle": {
            "1": {
                "material_id": "6976d020-18d1-4d46-9f3e-411189a1e230",
                "skew": [ 0.0, -0.02],
                "size": 0.4
           },
            "2": {
                "material_id": "6976d020-18d1-4d46-9f3e-411189a1e230",
                "skew": [ 0.1, -0.01],
                "size": 0.25
           }
       }
   }
    key = "head"
    pocket.set(key, settings)

    # Act
    head = pocket.getAsSubPocket(key)
    assert head is not None
    nozzle = head.getAsSubPocket("nozzle")

    nozzle_1 = nozzle.getAsSubPocket("1", None)
    nozzle_2 = nozzle.getAsSubPocket("2", None)
    nozzle_3 = nozzle.getAsSubPocket("3")

    nozzle_1.setAsInt("max_temperature", 120)
    nozzle_2.setAsFloat("size", 0.4)
    nozzle_3.setAsFloat("new_data", 0.4)

    # Assert
    assert nozzle_1 is not None
    assert nozzle_2 is not None
    updated_settings = pocket.get(key)
    assert "max_temperature" in updated_settings["nozzle"]["1"]
    assert 120 == updated_settings["nozzle"]["1"]["max_temperature"]
    assert 0.4 == updated_settings["nozzle"]["2"]["size"]
    assert 0.4 == updated_settings["nozzle"]["3"]["new_data"]
