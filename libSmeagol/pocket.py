import logging
import copy
import threading
import re
from typing import Optional, Dict, Union, Any, List, Tuple, Type

from libSmeagol.signal import Signal

log = logging.getLogger(__name__.split(".")[-1])


## This class handles the storing of settings and housekeeping of the settings.
#  To make sure, the store cannot be changed directly, whenever a value is retrieved, a copy is returned.
#  This way, it's made sure that structure isn't immediately done within the settings store itself.
#  When settings are changed (and differ from the current value), they will be saved after a short delay
class Pocket:

    ## Public

    ## Initializes the registry functionality
    #  @param preferences Allows to initialize with preferences (one time only)
    def __init__(self, preferences: Optional[Union[Dict[str, Any], "Pocket"]] = None) -> None:
        if preferences is None:
            self.__preferences = {}  # type: Dict[str, Any]
            # Small adjustment to allow to use a registry itself as an argument for the preferences
        elif isinstance(preferences, Pocket):
            log.info("Accessing the preferences dictionary: %r", preferences.__preferences)
            self.__preferences = copy.deepcopy(preferences.__preferences)
            assert isinstance(preferences, dict)
        else:
            self.__preferences = preferences

        self.__lock = threading.RLock()
        self.__decimal_number_pattern = re.compile(self.__DECIMAL_NUMBER_EXPRESSION)
        self.__on_changed = Signal(name="Pocket.__on_changed")

    ## Check if a key exists in this registry.
    # The normal get functions log warnings when unknown keys are retrieved,
    # so this can be used to test for existence of a key without causing log messages.
    #  @param key The setting
    #  @return bool True when the setting exists in this registry, false if not.
    def has(self, key: str) -> Any:
        with self.__lock:
            return key in self.__preferences

    #  A deepcopy is made so the setting can never be changed directly (and with that bypassing the trigger to save)
    #  @param key The setting
    #  @param default The default value to return
    #  @return Returns the setting value if found, or the specified default if not
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        result = self.__preferences.get(key, default)
        return copy.deepcopy(result)

    ## Gets the setting as an integer (cast). If the cast fails, the default value is returned.
    #  @param key The setting
    #  @param default The default value to return
    #  @retval default Returns the default value if setting is not found or the cast fails
    #  @retval int Returns the setting value as an integer
    def getAsInt(self, key: str, default: Optional[int] = None) -> Optional[int]:
        return self.__getAsType(key, default, int)

    ## Gets the setting as a float (cast). If the cast fails, the default value is returned.
    #  @param key The setting
    #  @param default The default value to return
    #  @retval default Returns the default value if setting is not found or the cast fails
    #  @retval float Returns the setting value as a float
    def getAsFloat(self, key: str, default: Optional[float] = None) -> Optional[float]:
        return self.__getAsType(key, default, float)

    ## Gets the setting as a string (cast). If the cast fails, the default value is returned.
    #  @param key The setting
    #  @param default The default value to return
    #  @retval default Returns the default value if setting is not found or the cast fails
    #  @retval int Returns the setting value as a string
    def getAsString(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.__getAsType(key, default, str)

    ## Gets the setting as a boolean (cast). If the cast fails, the default value is returned.
    #  @param key The setting
    #  @param default The default value to return
    #  @retval default Returns the default value if setting is not found or the cast fails
    #  @retval int Returns the setting value as a boolean
    def getAsBoolean(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        return self.__getAsType(key, default, bool)

    ## Gets the value of the key as a Pocket instance (registry is similar to a dict)
    #  @param key The setting
    #  @param default The default dictionary if no key was found to return
    #  @retval Pocket When the value is a dictionary, it will return a new Pocket class
    #          In case the data is not a dictionary, a copy of the "default" value will be returned
    def getAsSubPocket(self, key: str, default: Optional["Pocket"] = None) -> Optional["Pocket"]:
        if default is None:
            default = {}
        with self.__lock:
            value = None
            try:
                value = self.__preferences[key]
            except KeyError:
                value = copy.deepcopy(default)
                self.set(key, value)
            if isinstance(value, dict):
                sub_pocket = Pocket(value)
                # Implement that this pocket gets a signal when the sub-pocket changes
                sub_pocket.__on_changed.connect(self._handleOnChangeEvent)
                return sub_pocket
            else:
                log.warning(
                    "Getting key '%s' as pocket for pocket '%s' fails for not being a dictionary but a %s!",
                    key, self, type(value)
                )
                # Default behaviour is to return (copy) of the default
                return None

    def getAsRegistry(self, key: str, default: Optional["Pocket"] = None) -> Optional["Pocket"]:
        return self.getAsSubPocket(key, default)

    ## Gets the value of the key as a list
    #  @param key The setting
    #  @param default The default list if no key was found to return
    #  @retval list When the value is a list
    #          In case the data is not a list, a copy of the "default" value will be returned
    def getAsList(self, key: str, default: Optional[List[Any]] = None) -> Optional[List[Any]]:
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        else:
            log.warning("Getting key '%s' as registry fails for not being a list!", key)
            # Default behaviour is to return (copy) of the default
            return copy.deepcopy(default)

    ## Returns a copy of all the settings in the store
    #  @return Returns a copy of the settings as a dictionary
    def getAll(self) -> Dict[str, Any]:
        with self.__lock:
            return copy.deepcopy(self.__preferences)

    ## Converts values from the registry into a tuple
    #  @param requested_keys The list of keys which values should be returned as a tuple
    def getValuesFromKeysAsTuple(self, requested_keys: List[str]) -> Tuple[Any]:
        assert isinstance(requested_keys, list)

        value_list = []
        for key in requested_keys:
            if self.has(key):
                value_list.append(self.get(key))
            else:
                value_list.append(None)
        return tuple(value_list)

    ## Sets the value of a setting in the store and sets a flag that changes have been made so it will save those changes
    def set(self, key: str, value: Any) -> None:
        with self.__lock:
            if (key not in self.__preferences) or (self.__preferences[key] != value):
                self.__preferences[key] = value
                # Signal observers this registry has changed
                self._handleOnChangeEvent()

    ## Sets or updates the setting as an int type; if the casting fails, the value will be set as is
    #  @param key The setting to add or update
    #  @param value The value to set
    def setAsInt(self, key: str, value: Any) -> None:
        self.__setAsType(key, value, int)

    ## Sets or updates the setting as a float type; if the casting fails, the value will be set as is
    #  @param key The setting to add or update
    #  @param value The value to set
    def setAsFloat(self, key: str, value: Any) -> None:
        self.__setAsType(key, value, float)

    ## Sets or updates the setting as a string type; if the casting fails, the value will be set as is
    #  @param key The setting to add or update
    #  @param value The value to set
    def setAsString(self, key: str, value: Any) -> None:
        self.__setAsType(key, value, str)

    ## Sets or updates the setting as a boolean type; if the casting fails, the value will be set as is
    #  @param key The setting to add or update
    #  @param value The value to set
    def setAsBoolean(self, key: str, value: Any) -> None:
        self.__setAsType(key, value, bool)

    ## Sets or updates the settings as a Pocket
    #  @param key The setting to add or update
    #  @param value The value (registry) to set
    def setAsSubPocket(self, key: str, value: Any) -> None:
        if not isinstance(value, Pocket):
            raise ValueError("Trying to set key '%s' as a registry while it is not!", key)
        self.set(key, value.__preferences)

    def setAsRegistry(self, key: str, value: Any) -> None:
        self.setAsSubPocket(key, value)

    ## Sets or updates the settings as a list
    #  @param key The setting to add or update
    #  @param value The value (list) to set
    def setAsList(self, key: str, value: Any) -> None:
        if not isinstance(value, list):
            raise ValueError("Trying to set key '%s' as a list while it is not!", key)
        self.set(key, value)

    ## Removes a key from the dictionary
    #  @param key The setting to remove
    def delete(self, key: str) -> None:
        with self.__lock:
            if self.has(key):   # note: can only work with RLock
                del(self.__preferences[key])
                # Signal observers this registry has changed
                self._handleOnChangeEvent()

    ## Protected

    ## Handles an onChangeEvent which happens whenever a new value is added or an existing is changed
    def _handleOnChangeEvent(self) -> None:
        self.__on_changed.emit()

    ## Resets the dictionary
    def _setPreferences(self, preferences: Dict[str, Any]) -> None:
        with self.__lock:
            self.__preferences = preferences

    ## Private

    ## The regular expression to validate floating point numbers
    __DECIMAL_NUMBER_EXPRESSION = r"^-?\d+(,\d+)*(\.\d+(e\d+)?)?$"

    ## Gets the setting as the specified type. If the cast fails, the default value is returned.
    #  @param key The setting
    #  @param default The default value to return
    #  @param to_type type to cast the result into (except when returning the default)
    #  @return Returns the value as the new type or the default value in case of failure
    def __getAsType(self, key: str, default: Any, to_type: Type) -> Any:
        value = self.get(key, default)
        if value is None:
            return default
        else:
            return self.__castSafe(value, to_type, default)

    ## Sets the setting as the specified type. If the cast fails, the value is not set to prevent mayhem
    #  @param key The setting to update or add
    #  @param value The value to set
    #  @param to_type The type to set into
    def __setAsType(self, key: str, value: Any, to_type: Type) -> None:
        casted_value = self.__castSafe(value, to_type)
        if casted_value is None:
            raise ValueError("Cannot set %s as type %s" % (value, to_type))
        self.set(key, casted_value)

    ## Execute a safe typecast (if possible)
    #  Remarks: Handling conversion from string to boolean or vv needs to be addressed
    #  @param value The original value
    #  @param to_type The type to cast into
    #  @param default The default return value in case of casting failure
    #  @return Returns the value as the new type or the default value in case of failure
    def __castSafe(self, value: Any, to_type: Type, default: Any = None) -> Any:
        try:
            if (type(bool()) == to_type) and (type(str()) == type(value)):
                string_value = value.lower()
                if string_value in {"no", "false", "0"}:
                    return False
                if self.__decimal_number_pattern.match(value):
                    return int(self.__castSafe(value, float)) != 0
                else:
                    return True
            return to_type(value)
        except ValueError:
            log.warning("Cannot cast %s to type %s", value, to_type)
            return default

    ## default python function to get the string representation of the object.
    def __repr__(self) -> str:
        return "Pocket:" + str(self.__preferences)
