import time
import logging
import atexit

from threading import Thread
from libSmeagol.pocket import Pocket

log = logging.getLogger(__name__.split(".")[-1])


## This class handles the storing of settings and housekeeping of the settings.
#  To make sure, the store cannot be changed directly, whenever a value is retrieved, a copy is returned.
#  This way, it's made sure that structure aren't immediately done within the settings store itself.
#  When settings are changed (and differ from the current value), they will be saved after a short delay
class TimerPocket(Pocket):

    ## Public

    ## Initializes a thread for the registry to execute some action after some time has passed
    #  @param timer_interval The minimal interval between before the action is to be executed in seconds
    def __init__(self, timer_interval=5):
        super().__init__()
        self.__timer_interval = timer_interval
        self.__last_timer_check = None
        self.__running = False
        self.__thread = None

        # At exit, last call to action handler
        atexit.register(self.__callExecuteAction)

    ## Stops the thread from running, but does not stop the thread itself
    def stop(self):
        self.__running = False

    ## Protected

    ## Starts the timer check if not yet set or enforces this if reset_start is true
    def _startTimerCheck(self, *, reset_start=True):
        if reset_start or self.__last_timer_check is None:
            self.__last_timer_check = time.monotonic()

    ## Executes the action to be performed. Protected and must be overridden by derived classes
    def _executeAction(self):
        raise NotImplementedError

    ## Gets some identification string used for thread naming and possible identification
    #  @return Returns a string to identify the kind of registry
    def _getRegistryId(self):
        raise NotImplementedError

    ## (Re)starts the thread
    def _start(self):
        self.__clearLastTimerCheck()
        self.__running = True
        self.__thread.start()

    ## Creates and starts the timer thread and sets the initial timer check as well
    def _startTimerThread(self):
        # Start thread / run
        self.__startThread()
        self._startTimerCheck()

    ## Private

    ## During the run loop of the thread wait 1 second between activation
    __SLEEP_INTERVAL = 1

    ## Clears the timer check (effectively disabling the check, until it's set again)
    def __clearLastTimerCheck(self):
        self.__last_timer_check = None

    ## Wrapper that calls the derived function and disables the check afterwards
    def __callExecuteAction(self):
        self._executeAction()
        self.__clearLastTimerCheck()

    ## Starts the thread responsible for saving at regular intervals
    def __startThread(self):
        self.__running = True
        thread_name = self._getRegistryId()
        log.info("Setting up thread for " + thread_name)
        self.__thread = Thread(name=thread_name, target=self.__run, daemon=True)
        self.__thread.start()

    ## During the existence of the instance, the running thread will be calling this function.
    # Preferably this should be a private function, but as it is used as a callback, it needs to be public
    def __run(self):
        while self.__running:
            time.sleep(self.__SLEEP_INTERVAL)
            if self.__last_timer_check is not None:
                now = time.monotonic()
                last_timer_check = self.__last_timer_check + self.__timer_interval
                if last_timer_check < now:
                    self.__callExecuteAction()
                else:
                    time.sleep(last_timer_check - now)
