"""Skeleton code for sending to the bad bird site."""
import json
from os import path

import tweepy

from .output_utils import OutputRecord, OutputSkeleton

class BirdsiteSkeleton(OutputSkeleton):
    def __init__(self, secrets_dir, log):
        """Set up birdsite skeleton stuff."""
        super().__init__(secrets_dir, log)
        self.name = "BIRDSITE"

        self.handled_errors = {
            187: self.default_duplicate_handler,
        }

        self.ldebug("Retrieving CONSUMER_KEY...")
        with open(path.join(self.secrets_dir, "CONSUMER_KEY")) as f:
            CONSUMER_KEY = f.read().strip()

        self.ldebug("Retrieving CONSUMER_SECRET...")
        with open(path.join(self.secrets_dir, "CONSUMER_SECRET")) as f:
            CONSUMER_SECRET = f.read().strip()

        self.ldebug("Retrieving ACCESS_TOKEN...")
        with open(path.join(self.secrets_dir, "ACCESS_TOKEN")) as f:
            ACCESS_TOKEN = f.read().strip()

        self.ldebug("Retrieving ACCESS_SECRET...")
        with open(path.join(self.secrets_dir, "ACCESS_SECRET")) as f:
            ACCESS_SECRET = f.read().strip()

        self.ldebug("Looking for OWNER_HANDLE...")
        owner_handle_path = path.join(self.secrets_dir, "OWNER_HANDLE")
        if path.isfile(owner_handle_path):
            with open(owner_handle_path) as f:
                self.owner_handle = f.read().strip()
        else:
            self.ldebug("Couldn't find OWNER_HANDLE, unable to DM...")
            self.owner_handle = None

        self.auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

        self.api = tweepy.API(self.auth)

    def send(self, text):
        """Send birdsite message."""
        try:
            status = self.api.update_status(text)
            self.ldebug(f"Status object from tweet: {status}.")
            return TweetRecord(tweet_id=status._json["id"], text=text)

        except tweepy.TweepError as e:
            return self.handle_error(
                (f"Bot {self.bot_name} encountered an error when "
                 f"sending post {text} without media:\n{e}\n"),
                e)

    def send_with_one_media(self, text, filename):
        """Send birdsite message, with one media."""
        try:
            status = self.api.update_with_media(filename, status=text)
            self.ldebug(f"Status object from tweet: {status}.")
            return TweetRecord(tweet_id=status._json["id"], text=text,
                                             filename=filename)

        except tweepy.TweepError as e:
            return self.handle_error(
                (f"Bot {self.bot_name} encountered an error when "
                 f"sending post {text} with filename {filename}:\n{e}\n"),
                e)

    def send_with_many_media(self, text, filenames):
        """Upload media to birdsite, and send status and media."""

        media_ids = None
        try:
            self.ldebug(f"Uploading filenames {filenames}.")
            media_ids = [self.api.media_upload(filename).media_id_string for filename in filenames]
        except tweepy.TweepError as e:
            return handle_error(
                f"Bot {self.bot_name} encountered an error when uploading {filenames}:\n{e}\n",
                e)

        try:
            status = self.api.update_status(status=text, media_ids=media_ids)
            self.ldebug(f"Status object from tweet: {status}.")
            return TweetRecord(tweet_id=status._json["id"], text=text,
                                             media_ids=media_ids)

        except tweepy.TweepError as e:
            return handle_error(
                (f"Bot {self.bot_name} encountered an error when "
                 f"sending post {text} with media ids {media_ids}:\n{e}\n"),
                e)

    def send_dm_sos(self, message):
        """Send DM to owner if something happens."""
        if self.owner_handle is not None:
            try:
                _ = self.api.send_direct_message(user=self.owner_handle, text=message)

            except tweepy.TweepError as de:
                self.lerror(f"Error trying to send DM about error!: {de}")

        else:
            self.lerror("Can't send DM SOS, no owner handle.")

    def handle_error(self, message, e):
        """Handle error while trying to do something."""
        self.lerror(f"Got an error! {e}")

        # Handle errors if we know how.
        try:
            code = e[0]["code"]
            if code in self.handled_errors:
                self.handled_errors[code]
            else:
                self.send_dm_sos(message)

        except Exception:
            self.send_dm_sos(message)

        return TweetRecord(error=e)

class TweetRecord(OutputRecord):
    def __init__(self, tweet_id=None, text=None, filename=None, media_ids=[], error=None):
        """Create tweet record object."""
        super().__init__()
        self._type = self.__class__.__name__
        self.tweet_id = tweet_id
        self.text = text
        self.filename = filename
        self.media_ids = media_ids

        if error is not None:
            # So Python doesn't get upset when we try to json-dump the record later.
            self.error = json.dumps(error.__dict__)
            try:
                if isinstance(error.message, str):
                    self.error_message = error.message
                elif isinstance(error.message, list):
                    self.error_code = error.message[0]['code']
                    self.error_message = error.message[0]['message']
            except AttributeError:
                # fine, I didn't want it anyways.
                pass
