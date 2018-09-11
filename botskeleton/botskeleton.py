"""Skeleton for twitter bots. Spooky."""
import json
import time
from datetime import datetime
from os import path
from shutil import copyfile

import drewtilities as util
from clint.textui import progress

from .outputs.output_birdsite import BirdsiteSkeleton, TweetRecord
from .outputs.output_mastodon import MastodonSkeleton, TootRecord

class BotSkeleton():
    def __init__(self, secrets_dir=None, log_filename="log", history_filename=None,
                 bot_name="A bot", delay=3600):
        """Set up generic skeleton stuff."""

        self.log_filename = log_filename
        self.log = util.set_up_logging(log_filename=self.log_filename)

        if secrets_dir is None:
            msg = "Please provide secrets dir!"
            self.log.error(msg)
            raise BotSkeletonException(desc=msg)

        self.secrets_dir = secrets_dir
        self.bot_name = bot_name
        self.delay = delay

        if history_filename is None:
            history_filename = path.join(self.secrets_dir, f"{self.bot_name}-history.json")
        self.history_filename = history_filename

        self.extra_keys = {}
        self.history = self.load_history()

        self.outputs = {
            "birdsite": {
                "active": False,
                "obj_name": BirdsiteSkeleton,
                "obj": None,
            },
            "mastodon": {
                "active": False,
                "obj_name": MastodonSkeleton,
                "obj": None,
            },
        }

        self.setup_all_outputs()

    def setup_all_outputs(self):
        """Set up all output methods. Provide them credentials and anything else they need."""

        # The way this is gonna work is that we assume an output should be set up iff it has a
        # credentials_ directory under our secrets dir.
        for key in self.outputs.keys():
            credentials_dir = path.join(self.secrets_dir, f"credentials_{key}")
            if path.isdir(credentials_dir):
                self.outputs[key]["active"] = True
                # is this okay
                self.outputs[key]["obj"] = self.outputs[key]["obj_name"](credentials_dir, self.log)
                self.outputs[key]["obj"].bot_name = self.bot_name

        # Special-case birdsite for historical reasons.
        key = "birdsite"
        if not self.outputs[key]["active"] and \
                path.isfile(path.join(self.secrets_dir, "CONSUMER_KEY")):

            self.outputs[key]["active"] = True
            self.outputs[key]["obj"] = self.outputs[key]["obj_name"](self.secrets_dir, self.log)
            self.outputs[key]["obj"].bot_name = self.bot_name

    def send(self, text):
        """Post, without media, to all outputs."""
        # TODO there could be some annotation stuff here.
        record = IterationRecord(extra_keys=self.extra_keys)
        for key, output in self.outputs.items():
            if output["active"]:
                self.log.info(f"Output {key} is active, sending to it.")
                output_result = output["obj"].send(text)
                record.output_records[key] = output_result

            else:
                self.log.info(f"Output {key} is inactive. Not sending.")

        self.history.append(record)
        self.update_history()

        return record

    def send_with_one_media(self, text, filename):
        """Post, with one media item, to all outputs."""
        record = IterationRecord(extra_keys=self.extra_keys)
        for key, output in self.outputs.items():
            output_result = output["obj"].send_with_one_media(text, filename)
            record.output_records[key] = output_result

        self.history.append(record)
        self.update_history()

        return record

    def send_with_many_media(self, text, *filenames):
        """Post with several media. Provide filenames so outputs can handle their own uploads."""
        record = IterationRecord(extra_keys=self.extra_keys)
        for key, output in self.outputs.items():
            output_result = output["obj"].send_with_many_media(text, filenames)
            record.output_records[key] = output_result

        self.history.append(record)
        self.update_history()

        return record

    def nap(self):
        """Go to sleep for a bit."""
        self.log.info(f"Sleeping for {self.delay} seconds.")
        for _ in progress.bar(range(self.delay)):
            time.sleep(1)

    def store_extra_info(self, key, value):
        """Store some extra value in the tweet storage."""
        self.extra_keys[key] = value

    def store_extra_keys(self, d):
        """Store several extra values in the tweet storage."""
        new_dict = dict(self.extra_keys, **d)
        self.extra_keys = new_dict.copy()

    def update_history(self):
        """Update tweet history."""

        self.log.debug(f"Saving history. History is: \n{self.history}")

        jsons = []
        for item in self.history:
            json_item = item.__dict__

            # Convert sub-entries into JSON as well.
            output_records = {}
            for key, sub_item in item.output_records.items():
                if isinstance(sub_item, dict):
                    output_records[key] = sub_item
                else:
                    output_records[key] = sub_item.__dict__

            json_item["output_records"] = output_records

            jsons.append(json_item)

        if not path.isfile(filename):
            with open(filename, "a+") as f:
                f.close()

        with open(filename, "w") as f:
            json.dump(jsons, f, default=lambda x: x.__dict__().copy())

    def load_history(self):
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

                history = []
                for hdict in dicts:
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


class IterationRecord:
    """Record of one iteration. Includes records of all outputs."""
    def __init__(self, extra_keys={}):
        self._type = self.__class__.__name__
        self.timestamp = datetime.now().isoformat()
        self.extra_keys = extra_keys
        self.output_records = {}

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
            print(f"key {key} item {item}")
            obj.__dict__[key] = item

        print(f"obj {obj}")
        return obj


def rate_limited(max_per_hour, *args):
    """Rate limit a function."""
    return util.rate_limited(max_per_hour, *args)

def set_up_logging(log_filename):
    """Set up proper logging."""
    return util.set_up_logging(log_filename=log_filename)

def random_line(file_path):
    """Get random line from file."""
    return util.random_line(file_path=file_path)

class BotSkeletonException(Exception):
    """
    Generic Exception for errors in this project

    Attributes:
        desc  -- short message describing error
    """
    def __init__(self, desc:str) -> None:
        super(BotSkeletonException, self).__init__()
        self.desc = desc
