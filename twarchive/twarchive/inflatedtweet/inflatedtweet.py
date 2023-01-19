"""The InflatedTweet class and its helpers

The tweet is inflated in that all its supplemental data, like images,
are also downloaded and included.
"""

import base64
import datetime
import json
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
        date: typing.Optional[datetime.datetime] = None,
        date_original_format: str = "",
        full_text: str = "",
        full_html_strip_qts: str = "",
        full_html_link_qts: str = "",
        media: typing.List[TweetMediaAttachment] = None,
        entities: typing.Any = None,
        qts: typing.List[str] = None,
        rt_of: str = "",
        thread_parent_id: str = "",
        username: str = "",
        user_displayname: str = "",
        user_pfp: bytes = b"",
        retrieved_date: typing.Optional[datetime.datetime] = None,
        replyto_tweetid: str = "",
        replyto_username: str = "",
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
        self.media = media or []
        self.entities = entities
        self.qts = qts or []
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

    def jdump(
        self,
        fp: typing.Optional[typing.TextIO] = None,
        filepath: typing.Optional[str] = "",
    ):
        """Dump the inflated tweet to a JSON file

        We expect that users will commit the results to git,
        and indent=2 and sort_keys=True make diffs much nicer.
        """
        if not fp and not filepath:
            raise Exception("Must provide exactly one of fp= or filepath= to jdump")
        if fp:
            json.dump(self, fp, cls=InflatedTweetEncoder, indent=2, sort_keys=True)
        else:
            with open(filepath, "w") as fp:
                json.dump(self, fp, cls=InflatedTweetEncoder, indent=2, sort_keys=True)

    @classmethod
    def jload(
        cls,
        fp: typing.Optional[typing.TextIO] = None,
        filepath: typing.Optional[str] = "",
    ) -> "InflatedTweet":
        """Load an inflated tweet from a JSON file"""
        if not fp and not filepath:
            raise Exception("Must provide exactly one of fp= or filepath= to jload")
        if fp:
            infltweet = json.load(fp, cls=InflatedTweetDecoder)
        else:
            with open(filepath) as fp:
                infltweet = json.load(fp, cls=InflatedTweetDecoder)
        return infltweet


class InflatedTweetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, InflatedTweet):
            return obj.__dict__
        if isinstance(obj, Replacement):
            return obj.__dict__
        if isinstance(obj, TweetMediaAttachment):
            return obj.__dict__
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode()
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class InflatedTweetDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        """Automatically detect the shape of custom objects we have"""
        infltweet_fields = [
            "id",
            "date",
            "date_original_format",
            "full_text",
            "media",
            "entities",
            "username",
            "user_displayname",
            "user_pfp",
        ]
        is_inflated_tweet = all([f in obj for f in infltweet_fields])
        if is_inflated_tweet:
            return InflatedTweet(**obj)

        mediaatt_fields = ["width", "height", "alttext", "url", "data"]
        is_media_att = all([f in obj for f in mediaatt_fields])
        if is_media_att:
            return TweetMediaAttachment(**obj)

        return obj