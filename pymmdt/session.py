"""Module focused on the ``Session`` implementation.

Contains the following classes:
    ``Session``
"""

# Package Management
__package__ = 'pymmdt'

# Built-in Imports
from typing import Union, Dict, Optional, Any
import collections
import pathlib
import os
import shutil

# Third-party Imports
import pandas as pd
import numpy as np
import cv2

# Internal Imports
from .data_stream import DataStream
from .video import VideoDataStream
from .tabular import TabularDataStream
from .entry import StreamEntry, PointEntry

class Session:
    """Data Storage that contains the latest version of all data types.

    Attributes:
        records (Dict[str, DataSample]): Stores the latest version of a ``data_type`` sample
        or the output of a process.

    Todo:
        * Allow the option to store the intermediate samples stored in
        the session.

    """

    def __init__(
            self, 
            log_dir: Union[pathlib.Path, str],
            experiment_name: str,
            # clear_dir: bool = False
        ) -> None:
        """``Session`` Constructor.

        Args:
            log_dir (Union[pathlib.Path, str]): The directory to store information from the session.

            experiment_name (str): The name of the experiment, typically just using the name of the 
            participant/user.

            clear_dir (bool): To clear the sessions' directory.

        """
        # Converting the str to pathlib.Path
        if isinstance(log_dir, str):
            log_dir = pathlib.Path(log_dir)

        # Create the filepath of the experiment
        self.session_dir = log_dir / experiment_name

        # Create the folder if it doesn't exist 
        if not log_dir.exists():
            os.mkdir(log_dir)

        # Create the experiment dir
        if not self.session_dir.exists():
            os.mkdir(self.session_dir)

        # Create a record to the data
        self.records = {}
       
        # Keeping record of subsessions and elements changed
        self.subsessions = []

    def __getitem__(self, item:str) -> Any:
        """Get the item given the name of the ``Entry``.

        Args:
            item (str): The name of the requested name.

        Returns:
            Any: The last sample from that specified entry. To obtain
            the entire data stream, use ``session.records[item]``.
        """
        assert isinstance(item, str), f"{item} should be ``str``."

        # extract the entry
        entry = self.records[item]

        # Then ask the entry for the latest sample
        last_sample = entry.get_last_sample()
        return last_sample
    
    def create_stream(self, data_stream:DataStream) -> None:
        """create_stream.

        Args:
            data_stream (DataStream): The data stream to save in the 
            session.

        """
        assert isinstance(data_stream, DataStream)
        assert data_stream.name not in self.records.keys()

        # Create an entry
        entry = StreamEntry(
            dir=self.session_dir,
            name=data_stream.name,
            stream=data_stream,
        )
       
        # Append the stream
        self.records[entry.name] = entry
        
    def add_image(
            self, 
            name:str, 
            data:np.ndarray, 
            timestamp:Optional[pd.Timedelta]=None,
        ) -> None:
        """Log an image to an specified entry at an optional timestamp.

        Args:
            name (str): The name of the ``Entry`` to store it.

            data (np.ndarray): The image to store.

            timestamp (Optional[pd.Timedelta]): The optional timestamp
            to tag the image with.

        """

        # Detecting if this is the first time
        if name not in self.records.keys():

            # Create an entry
            entry = PointEntry(
                dir=self.session_dir,
                name=name,
                dtype='image',
                data=data,
                start_time=timestamp
            )

        # Not the first time
        else:
            # Extract the entry from the records
            entry = self.records[name]
            assert isinstance(entry.stream, VideoDataStream) or entry.dtype == 'image'

            # If everything is good, add the change to the track history
            # of the entry
            entry.append(
                data=data,
                timestamp=timestamp
            )

    def add_tabular(
            self, 
            name:str,
            data:Union[pd.Series, pd.DataFrame, Dict],
            timestamp:Optional[pd.Timedelta]=None,
        ) -> None:
        """add_tabular.

        Args:
            name (str): name
            data (Union[pd.Series, pd.DataFrame, Dict]): data
            timestamp (Optional[pd.Timedelta]): timestamp

        Returns:
            None:
        """

        # Ensure that the data is a dict
        if isinstance(data, (pd.Series, pd.DataFrame)):
            data_dict = data.to_dict()
        elif isinstance(data, dict):
            data_dict = data
        else:
            raise RuntimeError(f"{data} should be a dict, pd.DataFrame, or pd.Series")

        # Detecting if this is the first time
        if name not in self.records.keys():

            # Create an entry
            entry = PointEntry(
                dir=self.session_dir,
                name=name,
                dtype='tabular',
                data=data_dict,
                start_time=timestamp
            )

        # Not the first time
        else:
            # Extract the entry from the records
            entry = self.records[name]
            assert isinstance(entry.stream, TabularDataStream) or entry.dtype == 'tabular'

            # If everything is good, add the change to the track history
            # of the entry
            entry.append(
                data=data_dict,
                timestamp=timestamp
            )
 
    def create_subsession(self, name: str) -> 'Session':
        """create_subsession.

        Args:
            name (str): name

        Returns:
            'Session':
        """

        # Construct the subsession log_dir
        # and experiment_name
        log_dir = self.session_dir
        experiment_name = name
        
        # Create a new session instance
        subsession = self.__class__(
            log_dir,
            experiment_name,
            # self.clear_dir
        )

        # Store the subsession to this session
        self.subsessions.append(subsession)

        # Return the new session instance
        return self.subsessions[-1]

    def flush(self) -> None:
        """flush.

        Args:

        Returns:
            None:
        """

        # For all the entries, simply flush out each entry
        for entry in self.records.values():
            entry.flush()
     
    def close(self) -> None:
        """close.

        Args:

        Returns:
            None:
        """

        # Flush out the session data
        self.flush()
        
        # Then close all the entries
        for entry in self.records.values():
            entry.close()

        # Close all the subsessions
        for session in self.subsessions:
            session.close()
