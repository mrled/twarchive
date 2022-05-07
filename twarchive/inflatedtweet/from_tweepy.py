"""Creating an InflatedTweet from a tweepy.Tweet"""

import datetime
import typing

import requests
import tweepy

from twarchive import util
from twarchive.inflatedtweet import inflmedia
from twarchive.inflatedtweet.body import tweet_html_body
from twarchive.inflatedtweet.inflatedtweet import InflatedTweet


def inflated_tweet_from_tweepy(tweet: tweepy.models.Status):
    qts: typing.List[str] = []

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
    media = inflmedia.get_all_media(extended_entities, tweet.id_str, None)

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

    infltweet = InflatedTweet(
        tweet.id_str,
        tweet.created_at,
        tweet._json["created_at"],
        tweet.full_text,
        tweet_html_body(tweet.full_text, tweet.entities, False),
        tweet_html_body(tweet.full_text, tweet.entities, True),
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