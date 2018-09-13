"""Stuff used by output classes."""
import typing
from datetime import datetime
from logging import Logger

class OutputSkeleton:
    """Common stuff for output skeletons."""
    def __init__(self, secrets_dir: str, log: Logger) -> None:
        self.log = log
        self.secrets_dir = secrets_dir

        self.bot_name = ""
        self.handled_errors: typing.Dict[int, typing.Any] = {}

        # Output skeletons must implement these.
        self.cred_init: typing.Callable[[str, Logger], None]
        self.send: typing.Callable[[str], OutputRecord]
        self.send_with_one_media: typing.Callable[[str, str], OutputRecord]
        self.send_with_many_media: typing.Callable[[str, typing.Tuple[str, ...]], OutputRecord]

    def linfo(self, message: str) -> None:
        """Wrapped debug log with prefix key."""
        self.log.info(f"{self.bot_name}: {message}")

    def ldebug(self, message: str) -> None:
        """Wrapped debug log with prefix key."""
        self.log.debug(f"{self.bot_name}: {message}")

    def lerror(self, message: str) -> None:
        """Wrapped error log with prefix key."""
        self.log.error(f"{self.bot_name}: {message}")

    def default_duplicate_handler(self) -> None:
        """Default handler for duplicate status error."""
        self.linfo("Duplicate handler: who cares about duplicate statuses.")
        return

    def set_duplicate_handler(self, duplicate_handler: typing.Callable[..., None]) -> None:
        self.handled_errors[187] = duplicate_handler

class OutputRecord:
    """Record for an output occurrence."""
    def __init__(self) -> None:
        """Create tweet record object."""
        self._type = self.__class__.__name__
        self.timestamp = datetime.now().isoformat()

    def __str__(self) -> str:
        """Print object."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """repr object"""
        return str(self)

    @classmethod
    def from_dict(cls, obj_dict: typing.Dict[str, typing.Any]) -> "OutputRecord":
        """Get object back from dict."""
        obj = cls()
        for key, item in obj_dict.items():
            obj.__dict__[key] = item
        return obj
