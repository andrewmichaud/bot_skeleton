"""Skeleton code for sending to mastodon."""
import json
from logging import Logger
from os import path
from typing import List, Optional

import mastodon

from .output_utils import OutputRecord, OutputSkeleton

class MastodonSkeleton(OutputSkeleton):
    def __init__(self) -> None:
        """Set up mastodon skeleton stuff."""
        self.name = "MASTODON"

    def cred_init(self, secrets_dir: str, log: Logger, bot_name: str="") -> None:
        """Initialize what requires credentials/secret files."""
        super().__init__(secrets_dir, log, bot_name)

        self.ldebug("Retrieving ACCESS_TOKEN ...")
        with open(path.join(self.secrets_dir, "ACCESS_TOKEN")) as f:
            ACCESS_TOKEN = f.read().strip()

        # Instance base url optional.
        self.ldebug("Looking for INSTANCE_BASE_URL ...")
        instance_base_url_path = path.join(self.secrets_dir, "INSTANCE_BASE_URL")
        if path.isfile(instance_base_url_path):
            with open(instance_base_url_path) as f:
                self.instance_base_url = f.read().strip()
        else:
            self.ldebug("Couldn't find INSTANCE_BASE_URL, defaulting to mastodon.social.")
            self.instance_base_url = "https://mastodon.social"

        self.api = mastodon.Mastodon(access_token=ACCESS_TOKEN,
                                     api_base_url=self.instance_base_url)

    def send(self, text: str) -> OutputRecord:
        """Send mastodon message."""
        try:
            status = self.api.status_post(status=text)

            return TootRecord(toot_id=status["id"], text=text)

        except mastodon.MastodonError as e:
            return self.handle_error((f"Bot {self.bot_name} encountered an error when "
                                      f"sending post {text} without media:\n{e}\n"),
                                     e)

    def send_with_media(self, text: str, files: List[str], captions: List[str] = None
                        ) -> OutputRecord:
        """Upload media to mastodon, and send status and media, and captions if present."""
        try:
            self.ldebug(f"Uploading files {files}.")
            if captions is not None:
                if len(files) > len(captions):
                    captions.extend([""] * (len(files) - len(captions)))

                media_dicts = []
                for i, file in enumerate(files):
                    caption = captions[i]
                    media_dicts.append(self.api.media_post(file, description=caption))
            else:
                media_dicts = [self.api.media_post(file) for file in files]

            self.ldebug(f"Media ids {media_dicts}")

        except mastodon.MastodonError as e:
            return self.handle_error(
                f"Bot {self.bot_name} encountered an error when uploading {files}:\n{e}\n", e
            )

        try:
            status = self.api.status_post(status=text, media_ids=media_dicts)
            self.ldebug(f"Status object from toot: {status}.")
            return TootRecord(toot_id=status["id"], text=text, media_ids=media_dicts,
                              captions=captions)

        except mastodon.MastodonError as e:
            return self.handle_error((f"Bot {self.bot_name} encountered an error when "
                                      f"sending post {text} with media dicts {media_dicts}:"
                                      f"\n{e}\n"),
                                     e)

    # TODO find a replacement/find out how mastodon DMs work.
    # def send_dm_sos(self, message):
    #     """Send DM to owner if something happens."""

    def handle_error(self, message: str, e: mastodon.MastodonError) -> OutputRecord:
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
    def __init__(self, toot_id: str = None, text: str = None, files: List[str] = None,
                 media_ids: List[int] = [], error: mastodon.MastodonError = None,
                 captions: Optional[List[str]]=None
                 ) -> None:
        """Create toot record object."""
        super().__init__()
        self._type = self.__class__.__name__
        self.toot_id = toot_id
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
