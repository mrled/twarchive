"""JSON related code for inflated tweets"""

import base64
import datetime
import json

from twarchive.inflatedtweet.inflatedtweet import (
    InflatedTweet,
    Replacement,
    TweetMediaAttachment,
)


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
