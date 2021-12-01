"""Module focused on the ``Pipe`` implementation.

Contains the following classes:
    ``Pipe``

"""

# Package Management
__package__ = 'pymmdt'

# Built-in imports
from typing import Any, Dict
import copy

# Third-party imports
import pandas as pd

# Local Imports
from .process import Process
from .session import Session
from .collector import Collector

class Pipe:

    time = pd.Timedelta(0)
    session = None
    _processes = {}

    def __init__(self):
        ...

    def __repr__(self):

        # Construct a string that includes all the processes
        self_string = 'Pipe\n'

        # Combine the output string of the pipe and the processes.
        for process in self._processes.values():
            self_string += f'\t{process}\n'

        return self_string

    def __str__(self):
        return self.__repr__()

    def __setattr__(self, name:str, value:Any):
        """Unique ``__setattr__`` that catching Process instances.

        Args:
            name (str): The name of the variable.

            value (Any): The value of the variable. 

        Process instances added to the pipe are recorded for later use.
        This includes time matching, and giving processes additional
        useful attributes.
        
        """
        # Whenever the pipe has a processes added to it,
        # store in a list of processes.
        if isinstance(value, Process):
            self._processes[name] = value

        # Else, it's not a ``Process``, so just add it as normal
        else:
            super(Pipe, self).__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:

        # To avoid recursion, use the super __getattr__
        processes = super(Pipe, self).__getattribute__("_processes")
        if name == "_processes":
            return processes

        # If it is a process, obtain it from the ``_processes`` dict.
        if name in processes.keys():
            return processes[name]
        # Else, obtain it as normally
        else:
            super(Pipe, self).__getattribute__(name)

    def copy(self):
        """Create a deep copy of the pipe."""
        return copy.deepcopy(self)

    def attach_session(self, session: Session):

        # First make the session an attribute
        self.session = session

        # Then store the session into each process
        # for process in self._processes:
        #     process.attach_session(session)

    def attach_collector(self, collector: Collector):

        # First make the collector an attribute
        self.collector = collector

    def set_time(self, timestamp: pd.Timedelta):

        # Set its own time
        self.time = timestamp

        # Set the time for all processes
        for process in self._processes.values():
            setattr(process, 'time', copy.deepcopy(timestamp))

        return None

    def start(self):
        ...

    def step(self, data_samples: Dict[str, Any], which_new: str):
        ...

    def end(self):
        ...