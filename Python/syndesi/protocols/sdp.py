from ...wrappers.wrapper import Wrapper
from .primarydriver import PrimaryDriver

from ...interpreters import 

class SDP(PrimaryDriver):
    def __init__(self, wrapper : Wrapper):
        """
        SDP (Syndesi Device Protocol) compatible device

        Parameters
        ----------
        wrapper : Wrapper
        """
        self._wrapper = wrapper