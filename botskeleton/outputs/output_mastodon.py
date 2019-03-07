"""Skeleton code for sending to mastodon."""
import json
from logging import Logger
from os import path
from typing import Any, Callable, Dict, List, Optional

import mastodon

from .output_utils import OutputRecord, OutputSkeleton

class MastodonSkeleton(OutputSkeleton):
    def __init__(self) -> None:
        """Set up mastodon skeleton stuff."""
        self.name = "MASTODON"

    def cred_init(
            self,
            *,
            secrets_dir: str,
            log: Logger,
            bot_name: str="",
    ) -> None:
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

    def send(
            self,
            *,
            text: str,
    ) -> List[OutputRecord]:
        """
        Send mastodon message.

        :param text: text to send in post.
        :returns: list of output records,
            each corresponding to either a single post,
            or an error.
        """
        try:
            status = self.api.status_post(status=text)

            return [TootRecord(record_data={
                "toot_id": status["id"],
                "text": text
            })]

        except mastodon.MastodonError as e:
            return [self.handle_error((f"Bot {self.bot_name} encountered an error when "
                                      f"sending post {text} without media:\n{e}\n"),
                                     e)]

    def send_with_media(
            self,
            *,
            text: str,
            files: List[str],
            captions: List[str] = None,
    ) -> List[OutputRecord]:
        """
        Upload media to mastodon,
        and send status and media,
        and captions if present.

        :param text: post text.
        :param files: list of files to upload with post.
        :param captions: list of captions to include as alt-text with files.
        :returns: list of output records,
            each corresponding to either a single post,
            or an error.
        """
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
            return [self.handle_error(
                f"Bot {self.bot_name} encountered an error when uploading {files}:\n{e}\n", e
            )]

        try:
            status = self.api.status_post(status=text, media_ids=media_dicts)
            self.ldebug(f"Status object from toot: {status}.")
            return [TootRecord(record_data={
                "toot_id": status["id"],
                "text": text,
                "media_ids": media_dicts,
                "captions": captions
            })]

        except mastodon.MastodonError as e:
            return [self.handle_error((f"Bot {self.bot_name} encountered an error when "
                                      f"sending post {text} with media dicts {media_dicts}:"
                                      f"\n{e}\n"),
                                     e)]

    def perform_batch_reply(
            self,
            *,
            callback: Callable[..., str],
            lookback_limit: int,
            target_handle: str,
    ) -> List[OutputRecord]:
        """
        Performs batch reply on target account.
        Looks up the recent messages of the target user,
        applies the callback,
        and replies with
        what the callback generates.

        :param callback: a callback taking a message id,
            message contents,
            and optional extra keys,
            and returning a message string.
        :param target: the id of the target account.
        :param lookback_limit: a lookback limit of how many messages to consider.
        :returns: list of output records,
            each corresponding to either a single post,
            or an error.
        """
        self.log.info(f"Attempting to batch reply to mastodon user {target_handle}")

        records: List[OutputRecord] = []
        statuses = self.api.user_timeline(screen_name=target_handle, count=lookback_limit)
        for status in statuses:

            status_id = status.id
            # find possible replies we've made.
            our_statuses = self.api.user_timeline(since_id=status_id)
            in_reply_to_ids = list(map(lambda x: x.in_reply_to_status_id, our_statuses))
            if status_id not in in_reply_to_ids:
                message = callback(message_id=status_id, message=status.text, extra_keys={})

                full_message = f"@{target_handle} {message}"
                self.log.info(f"Replying {message} to status {status_id} from {target_handle}.")
                new_status = self.api.update_status(full_message, in_reply_to_status_id=status_id)

                records.append(TootRecord(record_data={
                    "tweet_id": new_status.id,
                    "text": full_message,
                }))
            else:
                self.log.info(f"Not replying to status {status_id} from {target_handle} "
                              f"- we already replied.")

        return records

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
    def __init__(
            self,
            *,
            record_data: Dict[str, Any]={},
            error: mastodon.MastodonError = None,
    ) -> None:
        """
        Create toot record object.

        :param record_data: data to use to generate a TootRecord.
        :param error: error encountered while posting,
            to generate a record with.
        """
        super().__init__()
        self._type = self.__class__.__name__
        self.toot_id = record_data.get("toot_id", "")
        self.text = record_data.get("text", "")
        self.files = record_data.get("files", [])
        self.media_ids = record_data.get("media_ids", [])
        self.captions = record_data.get("captions", [])

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
