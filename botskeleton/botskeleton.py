"""Skeleton for twitter bots. Spooky."""
import json
import pkg_resources
import time
from datetime import datetime
from logging import Logger
from os import path
from shutil import copyfile
from typing import Any, Callable, Dict, List

import drewtilities as util
from clint.textui import progress

from .outputs.output_birdsite import BirdsiteSkeleton, TweetRecord
from .outputs.output_mastodon import MastodonSkeleton, TootRecord
from .outputs.output_utils import OutputSkeleton, OutputRecord
from .error import BotSkeletonException

# Record of one round of media uploads.
class IterationRecord:
    """Record of one iteration. Includes records of all outputs."""
    def __init__(self, extra_keys: Dict[str, Any]={}) -> None:
        self._version = pkg_resources.require(__package__)[0].version
        self._type = self.__class__.__name__
        self.timestamp = datetime.now().isoformat()
        self.extra_keys = extra_keys
        self.output_records: Dict[str, OutputRecord] = {}

    def __str__(self) -> str:
        """Print object."""
        return str(self.__dict__)

    def __repr__(self) -> str:
        """repr object"""
        return str(self)

    @classmethod
    def from_dict(cls, obj_dict: Dict[str, Any]) -> "IterationRecord":
        """Get object back from dict."""
        obj = cls()
        for key, item in obj_dict.items():
            obj.__dict__[key] = item

        return obj


# Main class - handles sending and history management and such.
class BotSkeleton():
    def __init__(self, secrets_dir:str=None, log_filename:str=None, history_filename:str=None,
                 bot_name:str="A bot", delay:int=3600) -> None:
        """Set up generic skeleton stuff."""

        if secrets_dir is None:
            msg = "Please provide secrets dir!"
            raise BotSkeletonException(desc=msg)

        self.secrets_dir = secrets_dir
        self.bot_name = bot_name
        self.delay = delay

        if log_filename is None:
            log_filename = path.join(self.secrets_dir, "log")
        self.log_filename = log_filename
        self.log = util.set_up_logging(log_filename=self.log_filename)

        if history_filename is None:
            history_filename = path.join(self.secrets_dir, f"{self.bot_name}-history.json")
        self.history_filename = history_filename

        self.extra_keys: Dict[str, Any] = {}
        self.history = self.load_history()

        self.outputs = {
            "birdsite": {
                "active": False,
                "obj": BirdsiteSkeleton()
            },
            "mastodon": {
                "active": False,
                "obj": MastodonSkeleton()
            },
        }

        self._setup_all_outputs()

    ###############################################################################################
    ####        PUBLIC API METHODS                                                             ####
    ###############################################################################################
    def send(self, text: str) -> IterationRecord:
        """Post, without media, to all outputs."""
        # TODO there could be some annotation stuff here.
        record = IterationRecord(extra_keys=self.extra_keys)
        for key, output in self.outputs.items():
            if output["active"]:
                self.log.info(f"Output {key} is active, calling send on it.")
                entry: Any = output["obj"]
                output_result = entry.send(text=text)
                record.output_records[key] = output_result

            else:
                self.log.info(f"Output {key} is inactive. Not sending.")

        self.history.append(record)
        self.update_history()

        return record

    def send_with_one_media(self, text: str, filename: str, caption: str="") -> IterationRecord:
        """Post, with one media item, to all outputs."""
        record = IterationRecord(extra_keys=self.extra_keys)
        for key, output in self.outputs.items():
            if output["active"]:
                self.log.info(f"Output {key} is active, calling media send on it.")
                entry: Any = output["obj"]
                output_result = entry.send_with_media(text, files=[filename],
                                                      captions=[caption])
                record.output_records[key] = output_result
            else:
                self.log.info(f"Output {key} is inactive. Not sending with media.")

        self.history.append(record)
        self.update_history()

        return record

    def send_with_many_media(self, text: str, *filenames: str, captions: List[str]=[]
                             ) -> IterationRecord:
        """Post with several media. Provide filenames so outputs can handle their own uploads."""
        record = IterationRecord(extra_keys=self.extra_keys)
        for key, output in self.outputs.items():
            if output["active"]:
                self.log.info(f"Output {key} is active, calling media send on it.")
                entry: Any = output["obj"]
                output_result = entry.send_with_media(text=text, files=list(filenames),
                                                      captions=captions)
                record.output_records[key] = output_result
            else:
                self.log.info(f"Output {key} is inactive. Not sending with media.")

        self.history.append(record)
        self.update_history()

        return record

    def nap(self) -> None:
        """Go to sleep for a bit."""
        self.log.info(f"Sleeping for {self.delay} seconds.")
        for _ in progress.bar(range(self.delay)):
            time.sleep(1)

    def store_extra_info(self, key: str, value: Any) -> None:
        """Store some extra value in the tweet storage."""
        self.extra_keys[key] = value

    def store_extra_keys(self, d: Dict[str, Any]) -> None:
        """Store several extra values in the tweet storage."""
        new_dict = dict(self.extra_keys, **d)
        self.extra_keys = new_dict.copy()

    def update_history(self) -> None:
        """Update tweet history."""
        self.log.debug(f"Saving history. History is: \n{self.history}")

        jsons = []
        for item in self.history:
            json_item = item.__dict__

            # Convert sub-entries into JSON as well.
            json_item["output_records"] = self._parse_output_records(item)

            jsons.append(json_item)

        if not path.isfile(self.history_filename):
            open(self.history_filename, "a+").close()

        with open(self.history_filename, "w") as f:
            json.dump(jsons, f, default=lambda x: x.__dict__().copy(), sort_keys=True, indent=4)
            f.write("\n") # add trailing new line dump skips.

    def load_history(self) -> List["IterationRecord"]:
        """Load tweet history."""
        if path.isfile(self.history_filename):
            with open(self.history_filename, "r") as f:
                try:
                    dicts = json.load(f)

                except json.decoder.JSONDecodeError as e:
                    self.log.error(f"Got error \n{e}\n decoding JSON history, overwriting it.\n"
                                   f"Former history available in {self.history_filename}.bak")
                    copyfile(self.history_filename, f"{self.history_filename}.bak")
                    return []

                history: List[IterationRecord] = []
                for hdict_pre in dicts:

                    # repair any corrupted entries
                    hdict = _repair(hdict_pre)

                    if "_type" in hdict and \
                            hdict["_type"] == IterationRecord.__name__:
                        history.append(IterationRecord.from_dict(hdict))

                    # Be sure to handle legacy tweetrecord-only histories.
                    # Assume anything without our new _type (which should have been there from the
                    # start, whoops) is a legacy history.
                    else:
                        item = IterationRecord()

                        # Lift extra keys up to upper record (if they exist).
                        extra_keys = hdict.pop("extra_keys", {})
                        item.extra_keys = extra_keys

                        hdict_obj = TweetRecord.from_dict(hdict)

                        # Lift timestamp up to upper record.
                        item.timestamp = hdict_obj.timestamp

                        item.output_records["birdsite"] = hdict_obj

                        history.append(item)

                self.log.debug(f"Loaded history:\n {history}")

                return history

        else:
            return []

    ###############################################################################################
    ####        "PRIVATE" CLASS METHODS AND UTILITIES                                          ####
    ###############################################################################################
    def _setup_all_outputs(self) -> None:
        """Set up all output methods. Provide them credentials and anything else they need."""

        # The way this is gonna work is that we assume an output should be set up iff it has a
        # credentials_ directory under our secrets dir.
        for key in self.outputs.keys():
            credentials_dir = path.join(self.secrets_dir, f"credentials_{key}")

            # special-case birdsite for historical reasons.
            if key == "birdsite" and not path.isdir(credentials_dir) \
                    and path.isfile(path.join(self.secrets_dir, "CONSUMER_KEY")):
                credentials_dir = self.secrets_dir

            if path.isdir(credentials_dir):
                output_skeleton = self.outputs[key]

                output_skeleton["active"] = True

                obj: Any = output_skeleton["obj"]
                obj.cred_init(credentials_dir, self.log, bot_name=self.bot_name)

                output_skeleton["obj"] = obj

                self.outputs[key] = output_skeleton

    def _parse_output_records(self, item: IterationRecord) -> Dict[str, Any]:
        """Parse output records into dicts ready for JSON."""
        output_records = {}
        for key, sub_item in item.output_records.items():
            if isinstance(sub_item, dict):
                output_records[key] = sub_item
            else:
                output_records[key] = sub_item.__dict__

        return output_records


###################################################################################################
####        RE-EXPOSED PUBLIC API METHODS                                                      ####
###################################################################################################
def rate_limited(max_per_hour: int, *args: Any) -> Callable[..., Any]:
    """Rate limit a function."""
    return util.rate_limited(max_per_hour, *args)


def set_up_logging(log_filename: str) -> Logger:
    """Set up proper logging."""
    return util.set_up_logging(log_filename=log_filename)


def random_line(file_path: str) -> str:
    """Get random line from file."""
    return util.random_line(file_path=file_path)


###################################################################################################
####      "PRIVATE" MODULE METHODS, NOT INTENDED FOR PUBLIC USE                                ####
###################################################################################################
def _repair(record: Dict[str, Any]) -> Dict[str, Any]:
    """Repair a corrupted IterationRecord."""
    output_records = record.get("output_records")
    if record.get("_type") == "IterationRecord" and output_records is not None:
        birdsite_record = output_records.get("birdsite")

        # check for the bug
        if birdsite_record.get("_type") == "IterationRecord":

            # get to the bottom of the corrupted record
            while birdsite_record.get("_type") == "IterationRecord":
                sub_record = birdsite_record.get("output_records")
                birdsite_record = sub_record.get("birdsite")

            # add type
            birdsite_record["_type"] = TweetRecord.__name__

            # Lift extra keys, just in case.
            if "extra_keys" in birdsite_record:
                record_extra_values = record.get("extra_keys", {})
                for key, value in birdsite_record["extra_keys"]:
                    if key not in record_extra_values:
                        record_extra_values[key] = value

                record["extra_keys"] = record_extra_values

                del birdsite_record["extra_keys"]

            output_records["birdsite"] = birdsite_record

        # pull that correct record up to the top level, fixing corruption
        record["output_records"] = output_records

    return record
