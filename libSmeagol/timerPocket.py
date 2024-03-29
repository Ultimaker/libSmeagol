import time
import logging
import atexit

from threading import Event, Thread
from typing import Optional

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
    def __init__(self, timer_interval: int = 5) -> None:
        super().__init__()
        self.__timer_interval = timer_interval
        self.__last_timer_check = None  # type: Optional[float]
        self.__running = False
        self.__thread = None  # type: Optional[Thread]
        self.__thread_finished_event = Event()

        # At exit, last call to action handler
        atexit.register(self.__callExecuteAction)

    ## Stops the thread from running, but does not stop the thread itself
    def stop(self) -> None:
        self.__running = False
        self.__thread_finished_event.wait()

    ## Protected

    ## Starts the timer check if not yet set or enforces this if reset_start is true
    def _startTimerCheck(self, *, reset_start: bool = True) -> None:
        if reset_start or self.__last_timer_check is None:
            self.__last_timer_check = time.monotonic()

    ## Executes the action to be performed. Protected and must be overridden by derived classes
    def _executeAction(self) -> None:
        raise NotImplementedError

    ## Gets some identification string used for thread naming and possible identification
    #  @return Returns a string to identify the kind of registry
    def _getRegistryId(self) -> str:
        raise NotImplementedError

    ## (Re)starts the thread
    def _start(self) -> None:
        self.__clearLastTimerCheck()
        self._startTimerThread()

    ## Creates and starts the timer thread and sets the initial timer check as well
    def _startTimerThread(self) -> None:
        # Start thread / run
        self.__startThread()
        self._startTimerCheck()

    ## Private

    ## During the run loop of the thread wait 1 second between activation
    __SLEEP_INTERVAL = 1

    ## Clears the timer check (effectively disabling the check, until it's set again)
    def __clearLastTimerCheck(self) -> None:
        self.__last_timer_check = None

    ## Wrapper that calls the derived function and disables the check afterwards
    def __callExecuteAction(self) -> None:
        self._executeAction()
        self.__clearLastTimerCheck()

    ## Starts the thread responsible for saving at regular intervals
    def __startThread(self) -> None:
        self.__running = True
        thread_name = self._getRegistryId()
        log.info(f"Setting up thread: {thread_name}")
        self.__thread = Thread(name=thread_name, target=self.__run, daemon=True)
        self.__thread.start()

    ## During the existence of the instance, the running thread will be calling this function.
    # Preferably this should be a private function, but as it is used as a callback, it needs to be public
    def __run(self) -> None:
        try:
            while self.__running:
                time.sleep(self.__SLEEP_INTERVAL)
                if self.__last_timer_check is not None:
                    now = time.monotonic()
                    last_timer_check = self.__last_timer_check + self.__timer_interval
                    if last_timer_check < now:
                        self.__callExecuteAction()
                    else:
                        time.sleep(last_timer_check - now)
        finally:
            self.__thread_finished_event.set()
