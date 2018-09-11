"""Stuff used by output classes."""
from datetime import datetime

class OutputSkeleton:
    """Common stuff for output skeletons."""
    def __init__(self, secrets_dir, log):
        self.log = log
        self.secrets_dir = secrets_dir

        self.name = ""
        self.handled_errors = {}

    def linfo(self, message):
        """Wrapped debug log with prefix key."""
        self.log.info(f"{self.name}: {message}")

    def ldebug(self, message):
        """Wrapped debug log with prefix key."""
        self.log.debug(f"{self.name}: {message}")

    def lerror(self, message):
        """Wrapped error log with prefix key."""
        self.log.error(f"{self.name}: {message}")

    def default_duplicate_handler():
        """Default handler for duplicate status error."""
        self.linfo("Duplicate handler: who cares about duplicate statuses.")
        return

    def set_duplicate_handler(duplicate_handler):
        self.handled_errors[187] = duplicate_handler

class OutputRecord:
    """Record for an output occurrence."""
    def __init__(self):
        """Create tweet record object."""
        self._type = self.__class__.__name__
        self.timestamp = datetime.now().isoformat()

    def __str__(self):
        """Print object."""
        return str(self.__dict__)

    def __repr__(self):
        """repr object"""
        return str(self)

    @classmethod
    def from_dict(cls, obj_dict):
        """Get object back from dict."""
        obj = cls()
        for key, item in obj_dict.items():
            obj.__dict__[key] = item
        return obj
