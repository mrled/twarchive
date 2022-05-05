"""Subcommands and API calls

This needs a better name but I don't have one.
"""

import datetime
import json
import os
import re
import subprocess
import textwrap
import typing

import tweepy

from twarchive import inflatedtweet
from twarchive import logger


def authenticate(consumer_key: str, consumer_secret: str) -> tweepy.API:
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth)
    return api


def get_status_expanded(api: tweepy.API, tweetid: str) -> tweepy.models.Status:
    """Get a status"""
    tweet = api.get_status(
        tweetid,
        include_ext_alt_text=True,
        tweet_mode="extended",
    )
    return tweet


def tweetid2json(api: tweepy.API, tweetid: str, filename: str):
    tweet = get_status_expanded(api, tweetid)
    infltweet = inflatedtweet.InflatedTweet.from_tweet(tweet)
    with open(filename, "w") as fp:
        json.dump(infltweet, fp, cls=inflatedtweet.InflatedTweetEncoder, indent=2)


def tweet2data(
    api: tweepy.API,
    tweetid: str = "",
    tweet: tweepy.models.Status = None,
    force=False,
    rlevel=0,
    max_rlevel=20,
):
    """Save a tweet to site data

    Save its QTs as well.

    Arguments:
        api:                A tweepy.API that has already authenticated
        tweetid:            The ID of a tweet to save
        tweet:              An already retrieved Status object from tweepy
        force:              Redownload a tweet that already exists in site data.
        rlevel:             The recursion level of this function call.
                            This function calls itself for each QT, incrementing this value each time.
                            At some level we will stop, in case we are in some pathological case.
        max_rlevel:         The maximum number of QT or parent tweets to retrieve.
    """

    if (tweetid and tweet) or (not tweetid and not tweet):
        raise Exception("Must provide exactly one of tweet or tweetid")

    if not tweetid:
        tweetid = tweet.id_str

    filename = f"data/twarchive/{tweetid}.json"

    if os.path.exists(filename) and not force:
        logger.info(
            f"Tweet {tweetid} already exists in site data and force=False, not downloading"
        )
        return

    if rlevel > max_rlevel:
        logger.warning(
            f"WARNING! Recursion level of {rlevel}, refusing to download tweet {tweetid}"
        )
        return

    if not tweet:
        logger.info(f"Downloading tweet {tweetid}")
        tweet = get_status_expanded(api, tweetid)

    infltweet = inflatedtweet.InflatedTweet.from_tweet(tweet)
    with open(filename, "w") as fp:
        json.dump(infltweet, fp, cls=inflatedtweet.InflatedTweetEncoder, indent=2)
    rlevel += 1

    related_tweets = []
    related_tweets.extend(infltweet.qts)
    if infltweet.thread_parent_id:
        related_tweets.append(infltweet.thread_parent_id)
    try:
        related_tweets.append(tweet.retweeted_status.id_str)
    except AttributeError:
        pass

    for reltweet in related_tweets:
        try:
            tweet2data(
                api, tweetid=reltweet, force=force, rlevel=rlevel, max_rlevel=max_rlevel
            )
        except tweepy.errors.NotFound:
            # This appears to mean the tweet (or account) were intentionally deleted
            logger.warning(f"Could not find tweet with ID {reltweet}")
        except tweepy.errors.Forbidden as exc:
            # This appears to happen when the account was suspended
            exc_message = str(exc).replace("\n", " ")
            logger.warning(
                f"Not permitted to access tweet with ID {reltweet}: {exc_message}"
            )


def find_inline_tweets(content="./content") -> typing.List[str]:
    """Find tweets inlined with 'twarchiveTweet' or 'twarchiveThread' shortcodes in site content"""

    result = []

    rgcmd = [
        "rg",
        "--no-filename",
        "--no-line-number",
        "\{\{. twarchiveTweet .[0-9]+(-intentionallyinvalid)?",
        content,
    ]
    rg = subprocess.run(rgcmd, capture_output=True)
    outlines = rg.stdout.decode().strip().split("\n")
    for line in outlines:
        m = re.search(
            "{{. twarchiveTweet .(?P<tweetid>[0-9]+(:?-intentionallyinvalid)?)", line
        )
        result += [m["tweetid"]]

    rgcmd = [
        "rg",
        "--no-filename",
        "--no-line-number",
        "\{\{. twarchiveThread .[0-9]+(-intentionallyinvalid)?",
        content,
    ]
    rg = subprocess.run(rgcmd, capture_output=True)
    outlines = rg.stdout.decode().strip().split("\n")
    for line in outlines:
        m = re.search(
            "{{. twarchiveThread .(?P<tweetid>[0-9]+(:?-intentionallyinvalid)?)", line
        )
        result += [m["tweetid"]]

    return set(result)


def get_downloaded_tweets(twarchive="./data/twarchive") -> typing.List[str]:
    """Return a list of tweet IDs that have already been downloaded"""
    return [t.strip(".json") for t in os.listdir("data/twarchive")]


def showinlines():
    inlines = find_inline_tweets()
    print("Note: these tweets may QT other tweets, which are not listed here")
    for line in inlines:
        print(f"- {line}")


def inline2data(
    consumer_key: str, consumer_secret: str, max_rlevel: int, force: bool = False
):
    """Save tweets to data that have been inlined

    Does not redownload items already saved.
    """
    api = authenticate(consumer_key, consumer_secret)
    for tweetid in find_inline_tweets():
        if tweetid.endswith("-intentionallyinvalid"):
            logger.info(f"Skipping intentionally invalid tweet id {tweetid}")
        else:
            tweet2data(api, tweetid=tweetid, force=force, max_rlevel=max_rlevel)


def data2md():
    """For tweets that have been downloaded to the data directory, make a page for them in the content"""
    os.makedirs("content/twarchive", exist_ok=True)
    for tweet_json in os.listdir("data/twarchive/"):
        with open(f"data/twarchive/{tweet_json}") as tjfp:
            tweet = json.load(tjfp)
        tweet_date = datetime.datetime.strptime(tweet["date"], "%Y-%m-%dT%H:%M:%S%z")
        tweetid = tweet_json.strip("\.json")
        tweet_md_path = f"content/twarchive/{tweetid}.md"
        mdcontents = textwrap.dedent(
            f"""\
            ---
            tweetid: "{tweetid}"
            date: {tweet_date}
            ---
            """
        )
        with open(tweet_md_path, "w") as tmdfp:
            tmdfp.write(mdcontents)


def usertweets2data(
    api: tweepy.API,
    screen_name: str,
    max_rlevel: int,
    force: bool = False,
    retrieve_all: bool = False,
):
    """Save all of a user's tweets to data

    Arguments
    api:                A tweepy API object, already logged in
    screen_name:        The username to retrieve
    max_rlevel:         Max recursion level for QTs/replies
    force:              Download data again even if we already have it
    retrieve_all:       When True, go all the way to the beginning of the user's timeline.
                        When False (default), stop when encountering a tweet we've gotten before.
                        If force is True, this has no extra effect.
                        If force is False, the program will not redownload QTs or media
                        for tweets it already has, but will check all tweets the Twitter API lets us retrieve.
    """

    # Twitter API limit
    max_tweets_per_call = 200

    downloaded_tweets = get_downloaded_tweets()
    user_tweets = []
    oldest = None
    while True:
        logger.info(f"Retrieving tweets for @{screen_name} older than {oldest}")
        new_tweets = api.user_timeline(
            screen_name=screen_name,
            count=max_tweets_per_call,
            tweet_mode="extended",
            max_id=oldest,
        )
        if not new_tweets:
            break

        if force:
            oldest = str(new_tweets[-1].id - 1)
            continue

        unseen_tweets = [t for t in new_tweets if t.id_str not in downloaded_tweets]
        user_tweets.extend(unseen_tweets)
        if not retrieve_all and len(unseen_tweets) < len(new_tweets):
            break
        oldest = str(new_tweets[-1].id - 1)

    logger.info(
        f"Finished retrieving tweets for @{screen_name}, got {len(user_tweets)} tweets (force={force}, retrieve_all={retrieve_all})"
    )

    for tweet in user_tweets:
        tweet2data(api, tweet=tweet, force=force, max_rlevel=max_rlevel)
