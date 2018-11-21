"""Stuff used by output classes."""
from datetime import datetime
from logging import Logger
from typing import Any, Callable, Dict, List

class OutputSkeleton:
    """Common stuff for output skeletons."""
    def __init__(self, secrets_dir: str, log: Logger, bot_name: str) -> None:
        self.log = log
        self.secrets_dir = secrets_dir

        self.bot_name = bot_name
        self.handled_errors: Dict[int, Any] = {}

        # output skeletons must implement these
        self.cred_init: Callable[[str, Logger, str], None]
        self.send: Callable[[str], OutputRecord]
        self.send_with_media: Callable[[..., str, List[str], List[str]], OutputRecord]

    # helper methods
    def send_with_media_generic(self,
                                *,
                                text: str,
                                files: List[str],
                                captions: List[str],
                                ) -> List["OutputRecord"]:
        """Generic send with media method, relying on provided helper to do the actual work."""
        # must have helper
        if not hasattr(self, "send_with_media_helper"):
            self.lerror("Cannot call send_with_media_generic if send_with_media_helper"
                        " does not exist")
            return []

        # guarantee captions and files are of the same length
        if len(captions) < len(files):
            captions += [""] * (len(files) - len(captions))

        # check if we need to split media between multiple messages
        # put text just on first message
        if len(files) > self.max_media_per_post:
            records = []
            in_reply_to = None
            iterations = len(files) // self.max_media_per_post
            leftovers = len(files) % self.max_media_per_post

            for i in range(iterations):
                start = i * self.max_media_per_post
                end = (i+1) * self.max_media_per_post
                file_slice = files[start:end]
                caption_slice = captions[start:end]

                if in_reply_to is None:
                    txt = text
                else:
                    txt = None

                record = self.send_with_media_helper(text=txt,
                                                     files=file_slice,
                                                     captions=caption_slice,
                                                     in_reply_to=in_reply_to)

                in_reply_to = record.id
                records.append(record)

            # get leftovers
            if leftovers > 0:
                start = len(files) - leftovers
                file_slice = files[start:]
                caption_slice = captions[start:]

                record = self.send_with_media_helper(text=txt,
                                                     files=file_slice,
                                                     captions=caption_slice,
                                                     in_reply_to=in_reply_to)
                records.append(record)

            return records

        else:
            return [self.send_with_media_helper(text=text,
                                                files=files,
                                                captions=captions,
                                                in_reply_to=None)]

    def linfo(self, message: str) -> None:
        """Wrapped debug log with prefix key."""
        self.log.info(f"{self.bot_name}: {message}")

    def ldebug(self, message: str) -> None:
        """Wrapped debug log with prefix key."""
        self.log.debug(f"{self.bot_name}: {message}")

    def lerror(self, message: str) -> None:
        """Wrapped error log with prefix key."""
        self.log.error(f"{self.bot_name}: {message}")

class OutputRecord:
    """Record for an output occurrence."""
    def __init__(self) -> None:
        """Create output record object."""
        self._type = self.__class__.__name__
        self.timestamp = datetime.now().isoformat()

    def __str__(self) -> str:
        """Print object."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """repr object"""
        return str(self)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> "OutputRecord":
        """Get object back from dict."""
        obj = cls()
        for key, item in obj_dict.items():
            obj.__dict__[key] = item
        return obj
