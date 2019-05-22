import json
import logging
import os

from .timerPocket import TimerPocket

log = logging.getLogger(__name__.split(".")[-1])


## This class handles the storing of settings and housekeeping of the settings.
#  To make sure, the store cannot be changed directly, whenever a value is retrieved, a copy is returned.
#  This way, it's made sure that structure aren't immediately done within the settings store itself.
#  When settings are changed (and differ from the current value), they will be saved after a short delay
class NonVolatilePocket(TimerPocket):

    ## Public

    ## Initializes a thread for the registry to handle the automatic saving
    #  @param filename The filename to read/write the preferences (absolute path starts with '/')
    #  @param save_interval The minimal interval between saving of changes, with a default of 5 seconds
    def __init__(self, filename, save_interval=5):
        super().__init__(save_interval)
        # Variable needed for naming of thread to be used
        self.__preferences_file = os.path.join(self.__BASE_PATH, filename)
        # Load can be called after init (so the registry is initialized)
        self.__load()
        # Start the timer
        self._startTimerThread()

    ## Gets the filename, including the new path
    #  @return The fully qualified filename
    def getFilename(self):
        return self.__preferences_file

    ## Force to save the current preferences to disk.
    #  This function can be used to force the preferences to disk,
    #  and should only really be used when we are going to reboot directly after changing a setting.
    #  The system service needs to do this.
    def forceSave(self):
        self.__save()

    ## Stops the registry and erases all settings (remove file).
    #  @param restart_after_erase If true then the registryfile will be reopened and the thread started again
    def erase(self, *, restart_after_erase=True):
        self.stop()
        try:
            log.info("Wiping all registry keys...")
            os.remove(self.__preferences_file)
        except OSError as exception:
            log.error("Unable to remove settings file '%s', because %s", self.__preferences_file, exception.strerror)
            pass
        self._setPreferences({})
        if restart_after_erase:
            self.__load()
            self._start()

    ## Implements a special function that will erase all settings, except the keys mentioned in the keys_to_save list and add the extra settings at the end
    #  @param keys_to_backup The list of keys to backup prior to removing all settings
    #  @param settings_to_add The dictionary of key/values to add after te reset and restoration of the backed up key/values
    def backupAndSetup(self, keys_to_backup, settings_to_add):
        saved = {}
        log.info("Backing up keys...")
        for key in keys_to_backup:
            saved[key] = self.get(key)

        self.erase()

        log.info("Restoring settings...")
        for key, value in saved.items():
            self.set(key, value)

        log.info("Adding extra settings...")
        for key in settings_to_add.keys():
            self.set(key, settings_to_add[key])
        self.forceSave()

    ## Protected

    ## Executes the action to be performed. Protected and must be overridden by derived classes
    def _executeAction(self):
        self.__save()

    ## Gets some identification string used for thread naming and possible identification
    #  @return Returns a string to identify the kind of registry
    def _getRegistryId(self):
        basename = os.path.basename(self.__preferences_file)
        return log.name + ": '" + basename + "'"

    ## Handles an onChangeEvent which happens whenever a new value is added or an existing is changed
    def _handleOnChangeEvent(self):
        super()._handleOnChangeEvent()
        self._startTimerCheck()

    ## Private

    ## Default location for file storage
    __BASE_PATH = "/var/lib/griffin/"

    ## Loads the settings from the specified file in json format
    def __load(self):
        preferences = dict()
        if os.path.isfile(self.__preferences_file):
            log.info("Reading preferences from " + self.__preferences_file)
            try:
                with open(self.__preferences_file, "r") as f:
                    preferences = json.load(f)
            except Exception:
                log.warning("Error reading preferences file " + self.__preferences_file)
                preferences = dict()

        self._setPreferences(preferences)

    ## Save the settings store as a json file, including path creation if it does not exist
    def __save(self):
        log.info("Saving preferences to " + self.__preferences_file)
        preferences = self.getAll()
        if preferences is None:
            return

        directory = os.path.dirname(self.__preferences_file)
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            # First write the preference file to a new file on disk before we replace the old file.
            temp_filename = "%s.new" % (self.__preferences_file)
            with open(temp_filename, "w") as f:
                json.dump(preferences, f, indent=4)
                # Flush the file to disk, and fsync it so it is written to the filesystem.
                f.flush()
                os.fsync(f.fileno())
            # use os.replace to replace the old preference file with the new file. This is an atomic operation.
            os.replace(temp_filename, self.__preferences_file)
            # Open the directory containing the preference file, and fsync it. This forces the rename to disk.
            if hasattr(os, "O_DIRECTORY"):
                dir_fd = os.open(directory, os.O_DIRECTORY | os.O_RDONLY)
                os.fsync(dir_fd)
                os.close(dir_fd)
        except Exception:
            log.exception("Error writing preferences " + self.__preferences_file)
