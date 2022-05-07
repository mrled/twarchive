"""The InflatedTweet class and its helpers

The tweet is inflated in that all its supplemental data, like images,
are also downloaded and included.
"""

import base64
import datetime
import typing


class Replacement(typing.NamedTuple):
    """Text replacement for a tweet body."""

    start: int
    end: int
    replace: str


class TweetMediaAttachment:
    """A single media item like a photo"""

    def __init__(
        self,
        media_type: str,
        content_type: str,
        width: int,
        height: int,
        alttext: str,
        url: str,
        data: bytes,
    ):
        if media_type not in ["photo", "video", "animated_gif"]:
            raise ValueError(f"Unknown media_type {media_type}")
        self.media_type = media_type
        self.content_type = content_type
        self.width = width
        self.height = height
        self.alttext = alttext
        self.url = url
        if isinstance(data, str):
            self.data = base64.b64decode(data)
        else:
            self.data = data


class InflatedTweet:
    """A tweet with all supplemental data (like images) also downloaded"""

    def __init__(
        self,
        id: str,
        date: datetime.datetime,
        date_original_format: str,
        full_text: str,
        full_html_strip_qts: str,
        full_html_link_qts: str,
        media: typing.List[TweetMediaAttachment],
        entities: typing.Any,
        qts: typing.List[str],
        rt_of: str,
        thread_parent_id: str,
        username: str,
        user_displayname: str,
        user_pfp: bytes,
        retrieved_date: datetime.datetime,
        replyto_tweetid: str,
        replyto_username: str,
    ):
        self.id = id

        if isinstance(date, str):
            self.date = datetime.datetime.fromisoformat(date)
        else:
            self.date = date

        self.date_original_format = date_original_format
        self.full_text = full_text
        self.full_html_strip_qts = full_html_strip_qts
        self.full_html_link_qts = full_html_link_qts
        self.media = media
        self.entities = entities
        self.qts = qts
        self.rt_of = rt_of
        self.thread_parent_id = thread_parent_id
        self.username = username
        self.user_displayname = user_displayname

        if isinstance(user_pfp, str):
            self.user_pfp = base64.b64decode(user_pfp)
        else:
            self.user_pfp = user_pfp

        self.retrieved_date = retrieved_date

        self.replyto_tweetid = replyto_tweetid
        self.replyto_username = replyto_username

    @property
    def profileimg_b64(self):
        return base64.b64encode(self.profileimg).decode()
