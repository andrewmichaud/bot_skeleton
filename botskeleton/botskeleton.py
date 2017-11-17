"""Skeleton for twitter bots. Spooky."""
import logging
import json
import math
import random
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from os import path

import tweepy
from clint.textui import progress

LOG = logging.getLogger("root")
LAST_CALLED = {}


class BotSkeleton():
    def __init__(self, secrets_dir=None, bot_name="A bot", delay=0):
        """Authenticate and get access to API."""
        if secrets_dir is None:
            LOG.error("Please provide secrets dir!")
            raise Exception

        self.secrets_dir = secrets_dir
        self.bot_name = bot_name
        self.delay = delay

        self.extra_keys = {}
        self.history = self.load_history()

        LOG.debug("Retrieving CONSUMER_KEY...")
        with open(path.join(self.secrets_dir, "CONSUMER_KEY")) as f:
            CONSUMER_KEY = f.read().strip()

        LOG.debug("Retrieving CONSUMER_SECRET...")
        with open(path.join(self.secrets_dir, "CONSUMER_SECRET")) as f:
            CONSUMER_SECRET = f.read().strip()

        LOG.debug("Retrieving ACCESS_TOKEN...")
        with open(path.join(self.secrets_dir, "ACCESS_TOKEN")) as f:
            ACCESS_TOKEN = f.read().strip()

        LOG.debug("Retrieving ACCESS_SECRET...")
        with open(path.join(self.secrets_dir, "ACCESS_SECRET")) as f:
            ACCESS_SECRET = f.read().strip()

        LOG.debug("Looking for OWNER_HANDLE...")
        owner_handle_path = path.join(self.secrets_dir, "OWNER_HANDLE")
        if path.isfile(owner_handle_path):
            with open(owner_handle_path) as f:
                self.owner_handle = f.read().strip()
        else:
            LOG.debug("Couldn't find OWNER_HANDLE, unable to DM...")
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
            LOG.debug(f"Status object from tweet: {status}.")

        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                            f"sending post {text} without media:\n{e}\n")

        record = BotSkeleton.TweetRecord(tweet_id=status._json["id"], text=text,
                                         extra_keys=self.extra_keys)
        self.history.append(record)
        self.update_history()

        return record

    def send_with_one_media(self, text, filename):
        """Post, with one media."""
        try:
            status = self.api.update_with_media(filename, status=text)
            LOG.debug(f"Status object from tweet: {status}.")

        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"sending post {text} with filename {filename}:\n{e}\n")

        record = BotSkeleton.TweetRecord(tweet_id=status._json["id"], text=text,
                                         filename=filename, extra_keys=self.extra_keys)
        self.history.append(record)
        self.update_history()

        return record

    def send_with_media(self, text, media_ids):
        """Post, with media."""
        try:
            status = self.api.update_status(status=text, media_ids=media_ids)
            LOG.debug(f"Status object from tweet: {status}.")

        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"sending post {text} with media ids {media_ids}:\n{e}\n")

        record = BotSkeleton.TweetRecord(tweet_id=status._json["id"], text=text,
                                         media_ids=media_ids, extra_keys=self.extra_keys)
        self.history.append(record)
        self.update_history()

        return record

    def upload_media(self, *filenames):
        """Upload media, to be attached to post."""
        LOG.debug(f"Uploading filenames {filenames} to birdsite. Returning media ids.")

        try:
            return [self.api.media_upload(filename).media_id_string for filename in filenames]
        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when " +
                             f"uploading {filenames}:\n{e}\n")

    def send_dm_sos(self, message):
        """Send DM to owner if something happens."""
        if self.owner_handle is not None:
            try:
                status = self.api.send_direct_message(user=self.owner_handle, text=message)

            except (tweepy.TweepError, tweepy.RateLimitError) as de:
                LOG.error(f"Error trying to send DM about error!: {de}")

        else:
            LOG.error("Can't send DM SOS, no owner handle.")

    def nap(self):
        """Go to sleep for a bit."""
        LOG.info(f"Sleeping for {self.delay} seconds.")
        for s in progress.bar(range(self.delay)):
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

        LOG.debug(f"Saving history. History is: \n{self.history}")
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
                    LOG.error(f"Got error \n{e}\n decoding JSON history, overwriting it.")
                    return []

                history = [BotSkeleton.TweetRecord.from_dict(dict) for dict in dicts]
                LOG.debug(f"Loaded history\n {history}")

                return history

        else:
            return []


    class TweetRecord:
        def __init__(self, tweet_id=None, text=None, filename=None, media_ids=[],
                     extra_keys={}):
            """Create tweet record object."""
            self.timestamp = datetime.now().isoformat()
            self.tweet_id = tweet_id
            self.text = text
            self.filename = filename
            self.media_ids = media_ids

            self.extra_keys = extra_keys

        def __str__(self):
            """Print object."""
            return self.__dict__

        @classmethod
        def from_dict(cls, dict):
            """Get object back from dict."""
            obj = cls.__new__(cls)
            obj.__dict__ = dict.copy()
            return obj


def set_up_logging():
    """Set up proper logging."""
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)

    # Log everything verbosely to a file.
    file_handler = RotatingFileHandler(filename="log", maxBytes=1024000000, backupCount=10)
    verbose_form = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    file_handler.setFormatter(verbose_form)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Provide a stdout handler logging at INFO.
    stream_handler = logging.StreamHandler(sys.stdout)
    simple_form = logging.Formatter(fmt="%(message)s")
    stream_handler.setFormatter(simple_form)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(stream_handler)

    return logger


# TODO stolen from puckfetcher - should pull out into a lib.
# Modified from https://stackoverflow.com/a/667706
def rate_limited(max_per_hour, *args):
    """Decorator to limit function to N calls/hour."""
    min_interval = 3600.0 / float(max_per_hour)

    def _decorate(func):
        things = [func.__name__]
        things.extend(args)
        key = "".join(things)
        LOG.debug(f"Rate limiter called for {key}.")
        if key not in LAST_CALLED:
            LOG.debug(f"Initializing entry for {key}.")
            LAST_CALLED[key] = 0.0

        def _rate_limited_function(*args, **kargs):
            last_called = LAST_CALLED[key]
            now = time.time()
            elapsed = now - last_called
            remaining = min_interval - elapsed
            LOG.debug(f"Rate limiter last called for '{key}' at {last_called}.")
            LOG.debug(f"Remaining cooldown time for '{key}' is {remaining}.")

            if remaining > 0 and last_called > 0.0:
                LOG.info(f"Self-enforced rate limit hit, sleeping {remaining} seconds.")
                for i in progress.bar(range(math.ceil(remaining))):
                    time.sleep(1)

            LAST_CALLED[key] = time.time()
            ret = func(*args, **kargs)
            LOG.debug(f"Updating rate limiter last called for {key} to {now}.")
            return ret

        return _rate_limited_function
    return _decorate

def random_line(file_path):
    """Get random line from a file."""
    # Fancy alg from http://stackoverflow.com/a/35579149 to avoid loading full file.
    line_num = 0
    selected_line = ""
    with open(file_path) as f:
        while 1:
            line = f.readline()
            if not line:
                break
            line_num += 1
            if random.uniform(0, line_num) < 1:
                selected_line = line

    return selected_line.strip()
