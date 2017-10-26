"""Skeleton for twitter bots. Spooky."""

import logging
import os
import random
import sys
import time
from logging.handlers import RotatingFileHandler

import tweepy

LOG = logging.getLogger("root")
LAST_CALLED = {}


class BotSkeleton():
    def __init__(self, secrets_dir=None, bot_name="A bot"):
        """Authenticate and get access to API."""
        if secrets_dir is None:
            LOG.error("Please provide secrets dir!")
            raise Exception

        self.bot_name = bot_name

        LOG.debug("Retrieving CONSUMER_KEY...")
        with open(os.path.join(secrets_dir, "CONSUMER_KEY")) as f:
            CONSUMER_KEY = f.read().strip()

        LOG.debug("Retrieving CONSUMER_SECRET...")
        with open(os.path.join(secrets_dir, "CONSUMER_SECRET")) as f:
            CONSUMER_SECRET = f.read().strip()

        LOG.debug("Retrieving ACCESS_TOKEN...")
        with open(os.path.join(secrets_dir, "ACCESS_TOKEN")) as f:
            ACCESS_TOKEN = f.read().strip()

        LOG.debug("Retrieving ACCESS_SECRET...")
        with open(os.path.join(secrets_dir, "ACCESS_SECRET")) as f:
            ACCESS_SECRET = f.read().strip()

        LOG.debug("Looking for OWNER_HANDLE...")
        owner_handle_path = os.path.join(secrets_dir, "OWNER_HANDLE")
        if os.path.isfile(owner_handle_path):
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
        try:
            self.api.update_status(text)
        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.end_dm_sos(f"Bot {self.bot_name} encountered an error when" +
                            f"sending post {text} without media:\n{e}\n")

    def send_with_one_media(self, text, filename):
        """Post, with one media."""
        try:
            self.api.update_with_media(filename, status=text)
        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when" +
                             f"sending post {text} with filename {filename}:\n{e}\n")

    def send_with_media(self, text, media_ids):
        """Post, with media."""
        try:
            self.api.update_status(status=text, media_ids=media_ids)
        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when" +
                             f"sending post {text} with media ids {media_ids}:\n{e}\n")

    def upload_media(self, *filenames):
        """Upload media, to be attached to post."""
        LOG.debug(f"Uploading filenames {filenames} to birdsite. Returning media ids.")

        try:
            return [self.api.media_upload(filename).media_id_string for filename in filenames]
        except (tweepy.TweepError, tweepy.RateLimitError) as e:
            LOG.error(f"Got an error! {e}")
            self.send_dm_sos(f"Bot {self.bot_name} encountered an error when" +
                             f"uploading {filenames}:\n{e}\n")

    def send_dm_sos(self, message):
        """Send DM to owner if something happens."""
        if self.owner_handle is not None:
            try:
                self.api.send_direct_message(self.owner_handle, message)

            except (tweepy.TweepError, tweepy.RateLimitError) as de:
                LOG.error(f"Error trying to send DM about error!: {de}")

        else:
            LOG.error("Can't send DM SOS, no owner handle.")


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
                time.sleep(remaining)

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
