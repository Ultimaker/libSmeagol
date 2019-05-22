#   Author:  Thiago Marcos P. Santos
#   Author:  Christopher S. Case
#   Author:  David H. Bronke
#   Author:  Arjen Hiemstra
#   Author:  David Braam
#   Author:  Robin den Hertog
#   License: MIT

import inspect
from typing import Any, Callable, Dict, Set, Union, cast
from weakref import WeakKeyDictionary, WeakSet  # type: ignore


# TODO: Move this to it's own library, note this removes the embedded sync/async threaded signals.

##  Simple implementation of signals and slots.
#
#   Signals and slots can be used as a light weight event system. A class can
#   define signals that other classes can connect functions or methods to, called slots.
#   Whenever the signal is called, it will proceed to call the connected slots.
#
#   To create a signal, create an instance variable of type Signal. Other objects can then
#   use that variable's `connect()` method to connect methods, callables or signals to the
#   signal. To emit the signal, call `emit()` on the signal. Arguments can be passed along
#   to the signal, but slots will be required to handle them. When connecting signals to
#   other signals, the connected signal will be emitted whenever the signal is emitted.
#
#   Signal-slot connections are weak references and as such will not prevent objects
#   from being destroyed. In addition, all slots will be implicitly disconnected when
#   the signal is destroyed.
#
#   \warning It is imperative that the signals are created as instance variables, otherwise
#   emitting signals will get confused.
#
#   Based on http://code.activestate.com/recipes/577980-improved-signalsslots-implementation-in-python/
#
class Signal:

    ## Initialize the instance.
    #  @param kwargs The keyword arguments to pass along.
    def __init__(self, **kwargs) -> None:
        self.__functions = set()  # type: Set[Callable[[Any],None]]
        self.__methods = cast(Dict[object, Callable[[object, Any], None]], WeakKeyDictionary())
        self.__signals = cast(Set["Signal"], WeakSet())

    def __call__(self):
        raise NotImplementedError("Call emit() to emit a signal")

    ## Emit the signal, indirectly calling all connected slots.
    #  @param args The positional arguments to pass along.
    #  @param kwargs The keyword arguments to pass along.
    def emit(self, *args, **kwargs) -> None:
        # Call handler functions
        for func in self.__functions:
            func(*args, **kwargs)

        # Call handler methods
        for dest, funcs in self.__methods.copy().items():
            for func in funcs.copy():
                func(dest, *args, **kwargs)

        # Emit connected signals
        for signal in self.__signals.copy():
            signal.emit(*args, **kwargs)

    ##  Connect to this signal.
    #   \param connector The signal or slot to connect.
    def connect(self, connector: Union["Signal", Callable]) -> None:
        if isinstance(connector, Signal):
            if connector == self:
                return
            self.__signals.add(connector)
        elif inspect.ismethod(connector):
            if connector.__self__ not in self.__methods:  # type: ignore
                self.__methods[connector.__self__] = set()  # type: ignore

            self.__methods[connector.__self__].add(connector.__func__)  # type: ignore
        elif inspect.isfunction(connector):
            self.__functions.add(connector)
        else:
            raise AssertionError("connector was neither A Signal, A method nor A function: {}".format(str(type(connector))))

    ##  Disconnect from this signal.
    #   \param connector The signal or slot to disconnect.
    def disconnect(self, connector: Union[Callable, "Signal"]) -> None:
        if connector in self.__signals:
            self.__signals.remove(connector)
        elif inspect.ismethod(connector) and connector.__self__ in self.__methods:
            self.__methods[connector.__self__].remove(connector.__func__)
        else:
            if connector in self.__functions:
                self.__functions.remove(connector)

    ##  Disconnect all connected slots.
    def disconnectAll(self) -> None:
        self.__functions.clear()
        self.__methods.clear()
        self.__signals.clear()
