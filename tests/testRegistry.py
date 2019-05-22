import os
import sys
import unittest
import json
import time

sys.path.insert(0, os.path.abspath(sys.path[0]+"/.."))

from libSmeagol import Pocket, NonVolatilePocket


# Helper class for dictionaries
class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


## TestCase for functions exposed by the Pocket component
class PocketFileTestCase(unittest.TestCase):

    ## Full qualified path name for the json test file
    __PREFERENCES_FILE = "/tmp/test.json"
    ## Whether or not to display output (comparison original with expected, good for debugging tests)
    __DISPLAY_OUTPUT = False

    ## Clean up and create empty settings
    def setUp(self):
        self.__removePreferences()
        # Write settings every second
        self.__pocket = NonVolatilePocket(self.__PREFERENCES_FILE, 1)

    ## Clean up after tests
    def tearDown(self):
        self.__removePreferences()
        self.__pocket = None

    ## Remove the preferences file
    def __removePreferences(self):
        try:
            os.remove(self.__pocket.getFilename())
        except:
            pass

    ## Simple set value / wait for save / verify save test (implies get/set test)
    #  Because of the 1 it will be done first - if it fails, other test are kinda useless
    def test1SavePreference(self):
        # Arrange
        key = "TestKey"
        value = "dummy_value"

        # Act
        self.__pocket.setAsString(key, value)
        settings = self.__loadSettingsFromFile()

        # Assert
        self.assertEqual(value, settings[key])

    ## Test unknown key with default value
    #  Because of the 1 it will be done first - if it fails, other test are kinda useless
    def testUnkownKeySetting(self):
        # Arrange
        key = "KeyDoesNotExist"
        default_value = "the_default_value"

        # Act
        value = self.__pocket.get(key, default_value)

        # Assert
        self.assertEqual(value, default_value)

    ## Test getAsString conversions
    def testGetAsString(self):
        # Arrange
        settings = { "int": 101, "float": 13.501, "bool": True, "string": "test_case" }
        expected = { "int": "101", "float": "13.501", "bool": "True", "string": "test_case" }

        # Act
        self.__updatePocket(settings)

        # Assert
        for key, value in expected.items():
            actual_value = self.__pocket.getAsString(key)
            if self.__DISPLAY_OUTPUT:
                print("Expecting value %s for key %s with original value %s => actual value: %s" % (value, key, settings[key], actual_value))
            self.assertEqual(value, actual_value)

    ## Test setAsString conversions
    def testSetAsString(self):
        # Arrange
        settings = { "int": 101, "float": 13.501, "bool": True, "string": "test_case" }
        expected = { "int": "101", "float": "13.501", "bool": "True", "string": "test_case" }

        # Act
        for key, value in settings.items():
            self.__pocket.setAsString(key, value)

        # Assert
        for key, value in expected.items():
            actual_value = self.__pocket.get(key)
            if self.__DISPLAY_OUTPUT:
                print("Expecting value %s for key %s with original value %s => actual value: %s" % (value, key, settings[key], actual_value))
            self.assertEqual(value, actual_value)

    ## Test getAsBoolean conversions
    def testGetAsBoolean(self):
        # Arrange
        settings = { "int_zero": 0, "int_not_zero": 1, "int_positive": 1, "float": 13.501, "bool_true": True, "bool_false": False, "string_yes": "yes", "string_true": "true", "string_no": "no", "string_false": "false", "string_1": "1", "string_0": "0", "float_0": "0.00", "float_not_zero": "13.37" }
        expected = { "int_zero": False, "int_not_zero": True, "int_positive": True, "float": True, "bool_true": True, "bool_false": False, "string_yes": True, "string_true": True, "string_no": False, "string_false": False, "string_1": True, "string_0": False, "float_0": False, "float_not_zero": True }

        # Act
        self.__updatePocket(settings)

        # Assert
        for key, value in expected.items():
            actual_value = self.__pocket.getAsBoolean(key)
            if self.__DISPLAY_OUTPUT:
                print("Expecting value %s for key %s with original value %s => actual value: %s" % (value, key, settings[key], actual_value))
            self.assertEqual(value, actual_value)

    ## Test setAsBoolean conversions
    def testSetAsBoolean(self):
        # Arrange
        settings = { "int_zero": 0, "int_not_zero": 1, "int_positive": 1, "float": 13.501, "bool_true": True, "bool_false": False, "string_yes": "yes", "string_true": "true", "string_no": "no", "string_false": "false", "string_1": "1", "string_0": "0", "float_0": "0.00", "float_not_zero": "13.37" }
        expected = { "int_zero": False, "int_not_zero": True, "int_positive": True, "float": True, "bool_true": True, "bool_false": False, "string_yes": True, "string_true": True, "string_no": False, "string_false": False, "string_1": True, "string_0": False, "float_0": False, "float_not_zero": True }

        # Act
        for key, value in settings.items():
            self.__pocket.setAsBoolean(key, value)

        # Assert
        for key, value in expected.items():
            actual_value = self.__pocket.get(key)
            if self.__DISPLAY_OUTPUT:
                print("Expecting value %s for key %s with original value %s => actual value: %s" % (value, key, settings[key], actual_value))
            self.assertEqual(value, actual_value)

    ## Test some unable conversions (from string to int and vv)
    def testUnableConversions(self):
        # Arrange
        settings = { "not_a_number": "nan", "not_numeric": "abc" }
        expected = { "not_a_number": None, "not_numeric": None }

        # Act
        for key, value in settings.items():
            self.__pocket.setAsString(key, value)

        # Assert
        for key, value in expected.items():
            actual_value = self.__pocket.getAsInt(key)
            if self.__DISPLAY_OUTPUT:
                print("Expecting value %s for key %s with original value %s => actual value: %s" % (value, key, settings[key], actual_value))
            self.assertEqual(value, actual_value)

    ## Test setting a dictionary value as pocket
    def testSetAsPocket(self):
        # Arrange
        settings = { "int": 101, "float": 13.501, "bool": True, "string": "test_case" }
        key = "test_reg"
        len_settings = len(settings)

        # Act
        pocket = Pocket(settings)
        self.__pocket.setAsSubPocket(key, pocket)

        # Assert
        expected = self.__pocket.get(key)
        self.assertTrue(expected, dict)
        diff = DictDiffer(expected, settings)
        self.assertEqual(len_settings, len(expected))
        self.assertEqual(len_settings, len(diff.unchanged()))

    ## Test getting a pocket value
    def testGetAsPocket(self):
        # Arrange
        settings = { "int": 101, "float": 13.501, "bool": True, "string": "test_case" }
        key = "test_reg"
        len_settings = len(settings)

        # Act
        self.__pocket.set(key, settings)

        # Assert
        pocket = self.__pocket.getAsSubPocket(key)
        self.assertTrue(isinstance(pocket, Pocket))
        value = pocket.getAll()
        self.assertEqual(len_settings, len(value))
        diff = DictDiffer(value, settings)
        self.assertEqual(len_settings, len(diff.unchanged()))

    ## Test setting a pocket using a boolean value
    def testSetBooleanAsPocket(self):
        pocket = Pocket()
        
        with self.assertRaises(ValueError):
            pocket.setAsSubPocket(key="test_set_boolean_pocket", value=True)

    ## Test getting a pocket using from a boolean value
    def testGetAsPocketFromBoolean(self):
        # Arrange
        setting = True
        key = "test_get_boolean_pocket"
        expected = None

        # Act
        pocket = Pocket()
        pocket.set(key, setting)

        # Assert
        value = pocket.getAsSubPocket(key)
        self.assertEqual(expected, value)

    ## Test getting a pocket using from an unknown key
    def testGettingPocketFromUnknownKey(self):
        # Arrange
        key = "test_bogus_pocket"
        expected = { }

        # Act
        pocket = Pocket()
        value = pocket.getAsSubPocket(key)

        # Assert
        self.assertTrue(isinstance(value, Pocket))
        self.assertEqual(expected, value.getAll())

    ## Test setting a list
    def testSetAsList(self):
        # Arrange
        settings = [ "aap", "noot", "mies" ]
        key = "list_set_key"

        # Act
        self.__pocket.setAsList(key, settings)

        # Assert
        value = self.__pocket.get(key)
        self.assertTrue(isinstance(value, list))
        self.assertEqual(len(settings), len(value))
        self.assertTrue(settings == value)

    ## Test getting a list
    def testGetAsList(self):
        # Arrange
        settings = [ "aap", "noot", "mies" ]
        key = "list_get_key"

        # Act
        self.__pocket.set(key, settings)

        # Assert
        value = self.__pocket.getAsList(key)
        self.assertTrue(isinstance(value, list))
        self.assertEqual(len(settings), len(value))
        self.assertTrue(settings == value)

    ## Test setting a list using a boolean value
    def testSetBooleanAsList(self):
        pocket = Pocket()
        
        with self.assertRaises(ValueError):
            pocket.setAsList(key="test_set_boolean_list", value=True)

    ## Test get list from a boolean
    def testGetAsListFromBoolean(self):
        setting = True
        key = "test_get_boolean_list"

        pocket = Pocket()
        pocket.set(key, setting)

        value = pocket.getAsList(key)
        self.assertEqual([], value)

    ## Test getting a list using from an unknown key
    def testGettingListFromUnknownKey(self):
        # Arrange
        key = "test_bogus_list"
        expected = [ ]

        # Act
        pocket = Pocket()
        value = pocket.getAsList(key)

        # Assert
        self.assertTrue(isinstance(value, list))
        self.assertEqual(expected, value)

    ## Test nested pocket
    def testNestedPocket(self):
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
        self.__pocket.set(key, settings)

        # Act
        head = self.__pocket.getAsSubPocket(key)
        self.assertTrue(head is not None)
        nozzle = head.getAsSubPocket("nozzle")

        nozzle_1 = nozzle.getAsSubPocket("1", None)
        nozzle_2 = nozzle.getAsSubPocket("2", None)
        nozzle_3 = nozzle.getAsSubPocket("3")

        nozzle_1.setAsInt("max_temperature", 120)
        nozzle_2.setAsFloat("size", 0.4)
        nozzle_3.setAsFloat("new_data", 0.4)

        # Assert
        self.assertTrue(nozzle_1 is not None)
        self.assertTrue(nozzle_2 is not None)
        updated_settings = self.__pocket.get(key)
        self.assertTrue("max_temperature" in updated_settings["nozzle"]["1"])
        self.assertEqual(120, updated_settings["nozzle"]["1"]["max_temperature"])
        self.assertEqual(0.4, updated_settings["nozzle"]["2"]["size"])
        self.assertEqual(0.4, updated_settings["nozzle"]["3"]["new_data"])

    ## Loads the json file created by the pocket and return the contents as a dictionary
    #  @return Returns a dictionary instance of the jsond data file
    def __loadSettingsFromFile(self):
        time.sleep(2)
        settings = { }
        print("loading file " + self.__pocket.getFilename())
        with open(self.__pocket.getFilename(), "r") as f:
            settings = json.load(f)
        return settings

    ## Add settings to the pocket
    #  @param settings A dictionary of settings
    def __updatePocket(self, settings):
        for key, value in settings.items():
            self.__pocket.set(key, value)


## Main entry to create the instance and execute the test(s)
if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(PocketFileTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
