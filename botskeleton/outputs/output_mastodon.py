"""Skeleton code for sending to mastodon."""
import json
from os import path

import mastodon

from .output_utils import OutputRecord, OutputSkeleton

class MastodonSkeleton(OutputSkeleton):
    def __init__(self, secrets_dir, log):
        """Set up mastodon skeleton stuff."""
        super().__init__(secrets_dir, log)
        self.name = "MASTODON"

        self.ldebug("Retrieving ACCESS_TOKEN ...")
        with open(path.join(self.secrets_dir, "ACCESS_TOKEN")) as f:
            ACCESS_TOKEN = f.read().strip()

        # Instance base url optional.
        self.ldebug("Looking for INSTANCE_BASE_URL ...")
        instance_base_url_path = path.join(self.secrets_dir, "INSTANCE_BASE_URL")
        if path.isfile(instance_base_url_path):
            with open(instance_base_url_path) as f:
                INSTANCE_BASE_URL = f.read().strip()
        else:
            self.ldebug("Couldn't find INSTANCE_BASE_URL, defaulting to mastodon.social.")
            INSTANCE_BASE_URL = "https://mastodon.social"

        self.api = mastodon.Mastodon(
            access_token = ACCESS_TOKEN,
            api_base_url = INSTANCE_BASE_URL
        )

    def send(self, text):
        """Send mastodon message."""
        try:
            status = self.api.status_post(status=text)

            return TootRecord(toot_id=status["id"], text=text)

        except mastodon.MastodonError as e:
            return self.handle_error(
                (f"Bot {self.bot_name} encountered an error when "
                 f"sending post {text} without media:\n{e}\n"),
                e)

    def send_with_one_media(self, text, filename):
        """Send mastodon message, with one media."""
        filenames = [filename]
        return self.send_with_many_media(text, *filenames)

    def send_with_many_media(self, text, *filenames):
        """Upload media to mastodon, and send status and media."""
        media_ids = None
        try:
            self.ldebug(f"Uploading filenames {filenames}.")
            # TODO could probably put in some sensible, somewhat-useful descriptions on upload.
            media_ids = [self.api.media_post(filename)["id"] for filename in filenames]

        except mastodon.MastodonError as e:
            return self.handle_error(
                f"Bot {self.bot_name} encountered an error when uploading {filenames}:\n{e}\n",
                e)

        try:
            status = self.api.status_post(status=text)
            self.ldebug(f"Status object from toot: {status}.")
            return TootRecord(toot_id=status["id"], text=text, media_ids=media_ids)

        except mastodon.MastodonError as e:
            return self.handle_error(
                (f"Bot {self.bot_name} encountered an error when "
                 f"sending post {text} with media ids {media_ids}:\n{e}\n"),
                e)

    # TODO find a replacement/find out how mastodon DMs work.
    # def send_dm_sos(self, message):
    #     """Send DM to owner if something happens."""

    def handle_error(self, message, e):
        """Handle error while trying to do something."""
        self.lerror(f"Got an error! {e}")

        # Handle errors if we know how.
        try:
            code = e[0]["code"]
            if code in self.handled_errors:
                self.handled_errors[code]
            else:
                pass

        except Exception:
            pass

        return TootRecord(error=e)

class TootRecord(OutputRecord):
    def __init__(self, toot_id=None, text=None, filename=None, media_ids=[], error=None):
        """Create toot record object."""
        super().__init__()
        self._type = self.__class__.__name__
        self.toot_id = toot_id
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
