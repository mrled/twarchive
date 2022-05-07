"""Functionality that involves talking to the Twitter API"""

import os

import tweepy

from twarchive import hugo
from twarchive import logger
from twarchive.inflatedtweet.inflatedtweet import InflatedTweet
from twarchive.inflatedtweet.from_tweepy import inflated_tweet_from_tweepy


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
    infltweet = InflatedTweet.from_tweet(tweet)
    infltweet.jdump(filepath=filename)


def tweet2data(
    site: hugo.HugoSite,
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
        site:               A hugo.HugoSite object
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

    filename = os.path.join(site.data_twarchive, f"{tweetid}.json")

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

    infltweet = inflated_tweet_from_tweepy(tweet)
    infltweet.jdump(filepath=filename)
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
        tweet2data_continue_on_error(
            site,
            api,
            tweetid=reltweet,
            force=force,
            rlevel=rlevel,
            max_rlevel=max_rlevel,
        )


def tweet2data_continue_on_error(
    site: hugo.HugoSite,
    api: tweepy.API,
    tweetid: str = "",
    tweet: tweepy.models.Status = None,
    force=False,
    rlevel=0,
    max_rlevel=20,
):
    """Call tweet2data() with the parameters, and handle exceptions from missing/removed tweets

    Tweepy will raise exceptions if a tweet has been deleted or an account has gone private.
    Catch and log these exceptions, then continue.
    """
    try:
        tweet2data(
            site,
            api,
            tweetid=tweetid,
            tweet=tweet,
            force=force,
            rlevel=rlevel,
            max_rlevel=max_rlevel,
        )
    except tweepy.errors.NotFound:
        # This appears to mean the tweet (or account) were intentionally deleted
        logger.warning(f"Could not find tweet with ID {tweetid}")
    except tweepy.errors.Forbidden as exc:
        # This appears to happen when the account was suspended
        exc_message = str(exc).replace("\n", " ")
        logger.warning(
            f"Not permitted to access tweet with ID {tweetid}: {exc_message}"
        )


def usertweets2data(
    site: hugo.HugoSite,
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

    downloaded_tweets = hugo.get_downloaded_tweets(site)
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
        tweet2data(site, api, tweet=tweet, force=force, max_rlevel=max_rlevel)
