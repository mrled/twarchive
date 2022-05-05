"""The InflatedTweet class and its helpers

The tweet is inflated in that all its supplemental data, like images,
are also downloaded and included.
"""

import base64
import datetime
import json
import typing

import requests
import tweepy

from twarchive import util


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


def tweet_html_body(
    tweet: tweepy.models.Status,
    render_qt_link=False,
) -> str:
    """Create an HTML tweet body from the Tweepy object for a single tweet.

    - Text hashtags become links to search Twitter for the hashtag
    - Text URLs become links to the original URL (not the shortened one)
    - Text @mentions become links to the user's profile on Twitter
    - Text links to media get stripped out complete (they will be handled elsewhere)

    Arguments:
        tweet:          A Tweepy object representing a single tweet
        render_qt_link: If one of the URLs is a link to another tweet,
                        should it be rendered as a link?
                        If False, links to tweets will be stripped out completely,
                        so they can be included in full fidelity by other means.
                        If True, links to tweets will be rendered as regular <a> links.
    """
    replacements = {}
    for hashtag in tweet.entities.get("hashtags", []):
        hash = hashtag["text"]
        start, end = hashtag["indices"]
        replace = f'<a href="https://twitter.com/hashtag/{hash}">#{hash}</a>'
        replacements[start] = Replacement(start, end, replace)
    for url in tweet.entities.get("urls", []):
        expanded_url = url["expanded_url"]
        display_url = url["display_url"]
        start, end = url["indices"]
        if util.uri_is_tweet(expanded_url) and not render_qt_link:
            replace = ""
        else:
            replace = f'<a href="{expanded_url}">{display_url}</a>'
        replacements[start] = Replacement(start, end, replace)
    for mention in tweet.entities.get("user_mentions", []):
        start, end = mention["indices"]
        username = mention["screen_name"]
        replace = f'<a href="https://twitter.com/{username}">@{username}</a>'
        replacements[start] = Replacement(start, end, replace)
    for media in tweet.entities.get("media", []):
        start, end = media["indices"]
        replacements[start] = Replacement(start, end, "")

    htmlbody = tweet.full_text

    # Iterate through replacements in reverse
    # Means all the indexes will stay correct
    for key in sorted(replacements.keys(), reverse=True):
        r = replacements[key]
        pre = htmlbody[0 : r.start]
        post = htmlbody[r.end : len(htmlbody)]
        htmlbody = pre + r.replace + post

    # Clients may insert newlines, but we have to convert them to <br/> or else it won't display them properly
    htmlbody = htmlbody.replace("\n", "<br/>")

    return htmlbody


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

    @classmethod
    def from_tweet(cls, tweet: tweepy.models.Status):
        qts: typing.List[str] = []
        media: typing.List[TweetMediaAttachment] = []

        try:
            entities = tweet.entities
        except AttributeError:
            entities = {}
        for item in entities.get("urls"):
            if util.uri_is_tweet(item["expanded_url"]):
                qtid = util.tweeturi2tweetid(item["expanded_url"])
                qts += [qtid]

        try:
            extended_entities = tweet.extended_entities
        except AttributeError:
            extended_entities = {}
        for item in extended_entities.get("media", []):

            if item["type"] == "photo":
                w = item["sizes"]["small"]["w"]
                h = item["sizes"]["small"]["h"]
                alttext = item.get("media_alt_text", "")
                url = item["media_url_https"]
                mime = item.get("content_type", util.guess_mime_type(url))
                data = requests.get(url).content
                attachment = TweetMediaAttachment(
                    "photo", mime, w, h, alttext, url, data
                )
                media += [attachment]

            elif item["type"] == "video":
                w = item["sizes"]["small"]["w"]
                h = item["sizes"]["small"]["h"]
                alttext = item.get("media_alt_text", "")
                variants = {
                    int(v["bitrate"]): v
                    for v in item["video_info"]["variants"]
                    if "bitrate" in v
                }
                best_bitrate = max(variants.keys())
                variant = variants[best_bitrate]
                url = variant["url"]
                mime = variant.get("content_type", util.guess_mime_type(url))
                data = requests.get(url).content
                attachment = TweetMediaAttachment(
                    "video", mime, w, h, alttext, url, data
                )
                media += [attachment]

            elif item["type"] == "animated_gif":
                w = item["sizes"]["small"]["w"]
                h = item["sizes"]["small"]["h"]
                alttext = item.get("media_alt_text", "")
                variants = {
                    int(v["bitrate"]): v
                    for v in item["video_info"]["variants"]
                    if "bitrate" in v
                }
                best_bitrate = max(variants.keys())
                variant = variants[best_bitrate]
                url = variant["url"]
                mime = variant.get("content_type", util.guess_mime_type(url))
                data = requests.get(url).content
                attachment = TweetMediaAttachment(
                    "animated_gif", mime, w, h, alttext, url, data
                )
                media += [attachment]

            else:
                raise Exception(
                    f"Unknown item type {item['type']} trying to download media for tweet {tweet.id}"
                )

        try:
            rt_of = tweet.retweeted_status.id_str
        except AttributeError:
            rt_of = None

        user_pfp = requests.get(tweet.user.profile_image_url).content

        replyto_tweetid = None
        replyto_username = None
        if hasattr(tweet, "in_reply_to_status_id_str"):
            replyto_tweetid = tweet.in_reply_to_status_id_str
            replyto_username = tweet._json["in_reply_to_screen_name"]

        infltweet = cls(
            tweet.id_str,
            tweet.created_at,
            tweet._json["created_at"],
            tweet.full_text,
            tweet_html_body(tweet, False),
            tweet_html_body(tweet, True),
            media,
            tweet.entities,
            qts,
            rt_of,
            tweet._json["in_reply_to_status_id_str"],
            tweet.user.screen_name,
            tweet.user.name,
            user_pfp,
            datetime.datetime.utcnow(),
            replyto_tweetid,
            replyto_username,
        )

        return infltweet

    @property
    def profileimg_b64(self):
        return base64.b64encode(self.profileimg).decode()


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
