# timeout.py
# Sébastien Deriaz
# 20.11.2023

from enum import Enum
from typing import Union, Tuple
from time import time

class Timeout():
    DEFAULT_CONTINUATION_TIMEOUT = 5e-3

    class DataStrategy(Enum):
        DISCARD = 0 # If a timeout is reached, everything is trashed
        RETURN = 1 # If a timeout is reached, data is returned (timeout acts as a stop condition)
        STORE = 2 # If a timeout is reached, data is stored and returned on the next read() call

    _dataStrategyMap = {
        'discard' : DataStrategy.DISCARD,
        'return' : DataStrategy.RETURN,
        'store' : DataStrategy.STORE
    }

    class _TimeoutType(Enum):
        RESPONSE = 0
        CONTINUATION = 1
        TOTAL = 2
    class _State(Enum):
        WAIT_FOR_RESPONSE = 0
        CONTINUATION = 1

    def __init__(self, 
        response,
        on_response='discard',
        continuation=DEFAULT_CONTINUATION_TIMEOUT,
        on_continuation='return',
        total=None,
        on_total='discard') -> None:
        """
        A class to manage timeouts

        Timeouts are split in three categories :
        - response timeout : the "standard" timeout, (i.e the time it takes for
            a device to start transmitting data)
        - continuation timeout : the time between reception of
            data units (bytes or blocks of data)
        - total timeout : maximum time from start to end of transmission.
            This timeout can stop a communication mid-way. It is used to
            prevent a host from getting stuck reading a constantly streaming device
        
        Actions
        - discard : Discard all of data obtained during the read() call if the specified timeout if reached
        - return : Return all of the data read up to this point when the specified timeout is reached
        - store : Store all of the data read up to this point in a buffer. Data will be available at the next read() call

        Parameters
        ----------
        response : float
        on_response : str
            Action on response timeout ('discard', 'return' or 'store')
        continuation : float
        on_continuation : str
            Action on continuation timeout ('discard', 'return' or 'store')
        total : float
        on_total : str
            Action on total timeout ('discard', 'return' or 'store')
        """
        super().__init__()
        self._state = self._State.WAIT_FOR_RESPONSE
        for on_x in [on_response, on_continuation, on_total]:
            if on_x not in self._dataStrategyMap:
                raise ValueError(f"Invalid on_xxx value : {on_x}")
        self._response = response
        self._on_response = self._dataStrategyMap[on_response]
        self._continuation = continuation
        self._on_continuation = self._dataStrategyMap[on_continuation]
        self._total = total
        self._on_total = self._dataStrategyMap[on_total]
        self._queue_timeout = self._TimeoutType.CONTINUATION

    def initiate_read(self) -> Union[float, None]:
        """
        Initiate a read sequence.

        The maximum time that should be spent in the next byte read
        is returned

        Returns
        -------
        stop : bool
            Timeout is reached
        keep : bool
            True if data read up to this point should be kept
            False if data should be discarded
        timeout : float or None
            None is there's no timeout
        """
        print(f"Initiate read")
        self._start_time = time()
        self._state = self._State.WAIT_FOR_RESPONSE
        self._queue_timeout = self._TimeoutType.CONTINUATION
        self._last_timestamp = None
        return self._response

    def evaluate(self, timestamp : float) -> Tuple[bool, Union[float, None]]:
        #self._eval_time = time()
        stop = False
        self._data_strategy = None

        # First check if the timestamp is None, that would mean the timeout was reached in the queue
        if timestamp is None:
            # Set the data strategy according to the timeout that was given for the queue before
            match self._queue_timeout:
                case self._TimeoutType.RESPONSE:
                    self._data_strategy = self._on_response
                case self._TimeoutType.CONTINUATION:
                    self._data_strategy = self._on_continuation
                case self._TimeoutType.TOTAL:
                    self._data_strategy = self._on_total
            stop = True 
        else:
            # Check total
            if self._total is not None:
                if timestamp - self._start_time >= self._total:
                    stop = True
                    self._data_strategy = self._on_total
            # Check continuation
            elif self._continuation is not None and self._state == self._State.CONTINUATION and self._last_timestamp is not None:
                if timestamp - self._last_timestamp >= self._continuation:
                    stop = True
                    self._data_strategy = self._on_continuation
            # Check response time
            elif self._response is not None and self._state == self._State.WAIT_FOR_RESPONSE:
                response_time = timestamp - self._start_time
                if response_time >= self._response:
                    stop = True
                    self._data_strategy = self._on_response

        timeout = None
        # If we continue
        if not stop:
            # Update the state
            if self._state == self._State.WAIT_FOR_RESPONSE:
                self._state = self._State.CONTINUATION
            self._last_timestamp = timestamp
            # No timeouts were reached, return the next one
            # Return the timeout (state is always CONTINUATION at this stage)
            # Take the smallest between continuation and total
            if self._total is not None and self._continuation is not None:
                c = self._continuation
                t = self._start_time + self._total
                if c < t:
                    timeout = c
                    self._queue_timeout = self._TimeoutType.CONTINUATION
                else:
                    timeout = t
                    self._queue_timeout = self._TimeoutType.TOTAL
            elif self._total is not None:
                timeout = time() - (self._start_time + self._total)
                self._queue_timeout = self._TimeoutType.TOTAL
            elif self._continuation is not None:
                timeout = self._continuation
                self._queue_timeout = self._TimeoutType.CONTINUATION
                

        return stop, timeout

    def dataStrategy(self):
        return self._data_strategy
