"""Skeleton for twitter bots. Spooky."""
import json
import time
from datetime import datetime
from os import path

import drewtilities as util
import tweepy
from clint.textui import progress

class BotSkeleton():
    def __init__(self, secrets_dir=None, log_filename="log", bot_name="A bot", delay=0):
        """Authenticate and get access to API."""

        self.log_filename = log_filename
        self.log = util.set_up_logging(log_filename=self.log_filename)

        if secrets_dir is None:
            self.log.error("Please provide secrets dir!")
            raise Exception

        self.secrets_dir = secrets_dir
        self.bot_name = bot_name
        self.delay = delay

        self.extra_keys = {}
        self.history = self.load_history()

        self.log.debug("Retrieving CONSUMER_KEY...")
        with open(path.join(self.secrets_dir, "CONSUMER_KEY")) as f:
            CONSUMER_KEY = f.read().strip()

        self.log.debug("Retrieving CONSUMER_SECRET...")
        with open(path.join(self.secrets_dir, "CONSUMER_SECRET")) as f:
            CONSUMER_SECRET = f.read().strip()

        self.log.debug("Retrieving ACCESS_TOKEN...")
        with open(path.join(self.secrets_dir, "ACCESS_TOKEN")) as f:
            ACCESS_TOKEN = f.read().strip()

        self.log.debug("Retrieving ACCESS_SECRET...")
        with open(path.join(self.secrets_dir, "ACCESS_SECRET")) as f:
            ACCESS_SECRET = f.read().strip()

        self.log.debug("Looking for OWNER_HANDLE...")
        owner_handle_path = path.join(self.secrets_dir, "OWNER_HANDLE")
        if path.isfile(owner_handle_path):
            with open(owner_handle_path) as f:
                self.owner_handle = f.read().strip()
        else:
            self.log.debug("Couldn't find OWNER_HANDLE, unable to DM...")
            self.owner_handle = None

        self.auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

        self.api = tweepy.API(self.auth)

    def send(self, text):
        """Post, without media."""
        # TODO can probably make this error stuff an annotation or something.
        status = ""
        try:
            status = self.api.update_status(text)
            self.log.debug(f"Status object from tweet: {status}.")
            record = BotSkeleton.TweetRecord(tweet_id=status._json["id"], text=text,
                                             extra_keys=self.extra_keys)

        except tweepy.TweepError as e:
            self.log.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"sending post {text} without media:\n{e}\n")
            record = BotSkeleton.TweetRecord(text=text, error=str(e), extra_keys=self.extra_keys)

        self.history.append(record)
        self.update_history()

        return record

    def send_with_one_media(self, text, filename):
        """Post, with one media."""
        try:
            status = self.api.update_with_media(filename, status=text)
            self.log.debug(f"Status object from tweet: {status}.")
            record = BotSkeleton.TweetRecord(tweet_id=status._json["id"], text=text,
                                             filename=filename, extra_keys=self.extra_keys)

        except tweepy.TweepError as e:
            self.log.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"sending post {text} with filename {filename}:\n{e}\n")
            record = BotSkeleton.TweetRecord(text=text, error=str(e), extra_keys=self.extra_keys)

        self.history.append(record)
        self.update_history()

        return record

    def send_with_media(self, text, media_ids):
        """Post, with media."""
        try:
            status = self.api.update_status(status=text, media_ids=media_ids)
            self.log.debug(f"Status object from tweet: {status}.")
            record = BotSkeleton.TweetRecord(tweet_id=status._json["id"], text=text,
                                             media_ids=media_ids, extra_keys=self.extra_keys)

        except tweepy.TweepError as e:
            self.log.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"sending post {text} with media ids {media_ids}:\n{e}\n")
            record = BotSkeleton.TweetRecord(text=text, error=str(e), extra_keys=self.extra_keys)

        self.history.append(record)
        self.update_history()

        return record

    def upload_media(self, *filenames):
        """Upload media, to be attached to post."""
        self.log.debug(f"Uploading filenames {filenames} to birdsite. Returning media ids.")

        try:
            return [self.api.media_upload(filename).media_id_string for filename in filenames]
        except tweepy.TweepError as e:
            self.log.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"uploading {filenames}:\n{e}\n")
            record = BotSkeleton.TweetRecord(error=str(e), extra_keys=self.extra_keys)
            self.history.append(record)
            self.update_history()

    def send_dm_sos(self, message):
        """Send DM to owner if something happens."""
        if self.owner_handle is not None:
            try:
                _ = self.api.send_direct_message(user=self.owner_handle, text=message)

            except tweepy.TweepError as de:
                self.log.error(f"Error trying to send DM about error!: {de}")

        else:
            self.log.error("Can't send DM SOS, no owner handle.")

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
        filename = path.join(self.secrets_dir, f"{self.bot_name}-history.json")

        self.log.debug(f"Saving history. History is: \n{self.history}")
        jsons = [item.__dict__ for item in self.history]
        if not path.isfile(filename):
            with open(filename, "a+") as f:
                f.close()

        with open(filename, "w") as f:
            json.dump(jsons, f)

    def load_history(self):
        """Load tweet history."""
        filename = path.join(self.secrets_dir, f"{self.bot_name}-history.json")
        if path.isfile(filename):
            with open(filename, "r") as f:
                try:
                    dicts = json.load(f)

                except json.decoder.JSONDecodeError as e:
                    self.log.error(f"Got error \n{e}\n decoding JSON history, overwriting it.")
                    return []

                history = [BotSkeleton.TweetRecord.from_dict(dict) for dict in dicts]
                self.log.debug(f"Loaded history\n {history}")

                return history

        else:
            return []

    class TweetRecord:
        def __init__(self, tweet_id=None, text=None, filename=None, media_ids=[],
                     error=None, extra_keys={}):
            """Create tweet record object."""
            self.timestamp = datetime.now().isoformat()
            self.tweet_id = tweet_id
            self.text = text
            self.filename = filename
            self.media_ids = media_ids
            if error is not None:
                self.error_code = error["code"]
                self.error_message = error["message"]

            self.extra_keys = extra_keys

        def __str__(self):
            """Print object."""
            return self.__dict__

        @classmethod
        def from_dict(cls, obj_dict):
            """Get object back from dict."""
            obj = cls.__new__(cls)
            obj.__dict__ = obj_dict.copy()
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
