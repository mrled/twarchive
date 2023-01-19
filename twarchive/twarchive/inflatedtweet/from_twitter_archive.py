"""Creating an InflatedTweet from a tweepy.Tweet"""

from __future__ import annotations

import datetime
from tkinter import W
import typing

# WARNING: do _not_ import twarchive.twitterarchive from here, as it will result in circular imports
from twarchive import util
from twarchive.inflatedtweet import inflmedia
from twarchive.inflatedtweet.body import tweet_html_body
from twarchive.inflatedtweet.inflatedtweet import InflatedTweet

if typing.TYPE_CHECKING:
    from twarchive.twitterarchive import TwitterArchive


class TwitterArchiveTweetIsLowFidelityRetweetError(Exception):
    def __init__(self, tweetid: str):
        self.tweetid = tweetid

    def __str__(self):
        return f"Twitter archive tweet with ID {self.tweetid} is a low-fidelity retweet"


def twitter_archive_tweet_is_low_fidelity_retweet(tweet: typing.Dict) -> bool:
    """Determine whether a tweet from a Twitter archive is a low-fidelity retweet.

    - They do not provide high fidelity RTs, only tweets like "RT @whoever live laugh love amirite"
    - They do not even provide the original tweet ID for an RT
    - There is no indication that a tweet is an RT aside from starting with "RT"
    - Each tweet has a "retweeted" property, which simply appears to always be false
    """
    return tweet["full_text"].startswith("RT @")


def first_mention_from_tweet_text(text: str) -> str:
    """Given text of a tweet, extract the first @mention

    Kind of a fucking shitty hack lol
    """
    try:
        first_space_idx = text.index(" ")
    except ValueError:
        first_space_idx = len(text)
    try:
        first_colon_idx = text.index(":")
    except ValueError:
        first_colon_idx = len(text)
    username_end_idx = min(first_space_idx, first_colon_idx)
    replyto_username = text[1:username_end_idx]
    return replyto_username


def inflated_tweet_from_twitter_archive(
    tweet: typing.Dict,
    user_pfp: bytes,
    user_screenname: str,
    user_displayname: str,
    archive: "TwitterArchive",
) -> InflatedTweet:
    """Given a tweet dict and an unpacked Twitter archive, return an inflated tweet

    Notes:

    - This will throw TwitterArchiveTweetIsLowFidelityRetweetError if the tweet is a retweet.
      High-fidelity retweets must be retrieved from the Twitter API directly, unfortunately.
    - Each tweet has a 'truncated' property that always appears to be false
    - Each tweet has a 'retweeted' property that always apperas to be false
    """

    if twitter_archive_tweet_is_low_fidelity_retweet(tweet):
        raise TwitterArchiveTweetIsLowFidelityRetweetError(tweet["id_str"])
    rt_of = None

    # Parse the created_at value in the format that Twitter gives it to us
    created_at_dt = datetime.datetime.strptime(
        tweet["created_at"], "%a %b %d %H:%M:%S %z %Y"
    )

    # Put it back in the format that tweepy expects
    # tweet["created_at"] = created_at_dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    # tweepy_tweet = tweepy.Tweet(tweet)
    # Update: making a tweepy.Tweet this way just doesn't work well enough without talking to Twitter, argh

    qts: typing.List[str] = []

    entities = tweet.get("entities", {})
    for item in entities.get("urls"):
        if util.uri_is_tweet(item["expanded_url"]):
            qtid = util.tweeturi2tweetid(item["expanded_url"])
            qts += [qtid]

    extended_entities = tweet.get("extended_entitites", {})
    media = inflmedia.get_all_media(extended_entities, tweet["id_str"], archive)

    replyto_tweetid = None
    replyto_username = None
    if "in_reply_to_status_id_str" in tweet:
        replyto_tweetid = tweet["in_reply_to_status_id_str"]
        if "in_reply_to_screen_name" in tweet:
            replyto_username = tweet["in_reply_to_screen_name"]
        elif tweet["full_text"].startswith("@"):
            replyto_username = first_mention_from_tweet_text(tweet["full_text"])
        else:
            raise Exception(
                "Can't figure out a username this tweet is replying to, lol"
            )

    infltweet = InflatedTweet(
        tweet["id_str"],
        created_at_dt,
        tweet["created_at"],
        tweet["full_text"],
        tweet_html_body(tweet["full_text"], tweet["entities"], False),
        tweet_html_body(tweet["full_text"], tweet["entities"], True),
        media,
        tweet["entities"],
        qts,
        rt_of,
        replyto_tweetid,
        user_screenname,
        user_displayname,
        user_pfp,
        archive.generation_date,
        replyto_tweetid,
        replyto_username,
    )

    return infltweet
