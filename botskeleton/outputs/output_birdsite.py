"""Skeleton code for sending to the bad bird site."""
import json
from logging import Logger
from os import path
from typing import Any, Callable, List, Optional

import tweepy

from .output_utils import OutputRecord, OutputSkeleton


class BirdsiteSkeleton(OutputSkeleton):
    def __init__(self) -> None:
        """Set up birdsite skeleton stuff."""
        self.name = "BIRDSITE"

        self.handled_errors = {
            187: self.default_duplicate_handler,
        }

    def cred_init(self, secrets_dir: str, log: Logger, bot_name: str="") -> None:
        """Initialize what requires credentials/secret files."""
        super().__init__(secrets_dir, log, bot_name)

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
            self.owner_handle = ""

        self.auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

        self.api = tweepy.API(self.auth)

    def send(self, text: str) -> OutputRecord:
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

    def send_with_media(self, text: str, files: List[str], captions: List[str]=None
                        ) -> OutputRecord:
        """Upload media to birdsite, and send status and media, and captions if present."""

        # upload media
        media_ids = None
        try:
            self.ldebug(f"Uploading files {files}.")
            media_ids = [self.api.media_upload(file).media_id_string for file in files]
        except tweepy.TweepError as e:
            return self.handle_error(
                f"Bot {self.bot_name} encountered an error when uploading {files}:\n{e}\n",
                e)

        # apply captions, if present
        self.handle_caption_upload(media_ids, captions)

        # send status
        try:
            status = self.api.update_status(status=text, media_ids=media_ids)
            self.ldebug(f"Status object from tweet: {status}.")
            return TweetRecord(tweet_id=status._json["id"], text=text, media_ids=media_ids,
                               captions=captions, files=files)

        except tweepy.TweepError as e:
            return self.handle_error(
                (f"Bot {self.bot_name} encountered an error when "
                 f"sending post {text} with media ids {media_ids}:\n{e}\n"),
                e)

    def send_dm_sos(self, message: str) -> None:
        """Send DM to owner if something happens."""
        if self.owner_handle:
            try:
                self.api.send_direct_message(user=self.owner_handle, text=message)

            except tweepy.TweepError as de:
                self.lerror(f"Error trying to send DM about error!: {de}")

        else:
            self.lerror("Can't send DM SOS, no owner handle.")

    def handle_error(self, message: str, e: tweepy.TweepError) -> OutputRecord:
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

    def default_duplicate_handler(self) -> None:
        """Default handler for duplicate status error."""
        self.linfo("Duplicate handler: who cares about duplicate statuses.")
        return

    def set_duplicate_handler(self, duplicate_handler: Callable[..., None]) -> None:
        self.handled_errors[187] = duplicate_handler

    def handle_caption_upload(self, media_ids: List[str], captions: Optional[List[str]]) -> None:
        """Handle uploading all captions."""
        if captions is None:
            return

        if len(media_ids) > len(captions):
            captions.extend([""] * (len(media_ids) - len(captions)))

        for i, media_id in enumerate(media_ids):
            caption = captions[i]
            self.upload_caption(media_id=media_id, caption=caption)

    # taken from https://github.com/tweepy/tweepy/issues/716#issuecomment-398844271
    def upload_caption(self, media_id: str, caption: str) -> Any:
        post_data = {
            "media_id": media_id,
            "alt_text": {
                "text": caption,
            },
        }

        metadata_path = "/media/metadata/create.json"

        return tweepy.binder.bind_api(api=self.api, path=metadata_path, method="POST",
                                      allowed_param=[], require_auth=True, upload_api=True
                                      )(post_data=json.dumps(post_data))

class TweetRecord(OutputRecord):
    def __init__(self, tweet_id: str=None, text: str=None, files: List[str]=[],
                 media_ids: List[str]=[], captions: Optional[List[str]]=[],
                 error: tweepy.TweepError=None
                 ) -> None:
        """Create tweet record object."""
        super().__init__()
        self._type = self.__class__.__name__
        self.tweet_id = tweet_id
        self.text = text
        self.files = files
        self.media_ids = media_ids
        self.captions = captions

        if error is not None:
            # So Python doesn't get upset when we try to json-dump the record later.
            self.error = json.dumps(error.__dict__)
            try:
                if isinstance(error.message, str):
                    self.error_message = error.message
                elif isinstance(error.message, list):
                    self.error_code = error.message[0]["code"]
                    self.error_message = error.message[0]["message"]
            except AttributeError:
                # fine, I didn't want it anyways.
                pass
