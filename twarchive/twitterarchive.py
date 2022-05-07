"""Functionality related to a downloaded Twitter archive

Twitter allows account owners to download all their own tweets,
as well as a bunch of other data,
in an archive file.
We can use any archive files as a definitive copy of a tweet.

Note that a tweet found in an archive should _never_ be redownloaded,
at least as long as Twitter does not permit edits.
"""

import json
import os
import re
import typing

import tweepy

from twarchive import logger, twitterapi
from twarchive.inflatedtweet.from_twitter_archive import (
    inflated_tweet_from_twitter_archive,
    twitter_archive_tweet_is_low_fidelity_retweet,
)
from twarchive.inflatedtweet.inflatedtweet import InflatedTweet
from twarchive.inflatedtweet.infltweet_json import InflatedTweetEncoder


class TwitterArchive(typing.NamedTuple):
    """An on-disk, extracted Twitter archive"""

    path: str
    profilejs: str
    tweetjs: str
    accountjs: str
    profilemedia: str
    tweetmedia: str

    @classmethod
    def frompath(cls, p: str) -> "TwitterArchive":
        data = os.path.join(p, "data")
        archive = cls(
            p,
            os.path.join(data, "profile.js"),
            os.path.join(data, "tweet.js"),
            os.path.join(data, "account.js"),
            os.path.join(data, "profile_media"),
            os.path.join(data, "tweet_media"),
        )
        return archive


def parse_twitter_window_YTD_bullshit(
    archivefile: str,
) -> typing.Union[typing.Dict, typing.List]:
    """The fucking Twitter archive is in a deranged format for no good reason."""
    with open(archivefile) as afp:
        contents = afp.read()
    unfucked = re.sub(
        r"^window\.YTD\.[a-zA-Z0-9_]+\.part[a-zA-Z0-9_]+ = ", "", contents
    )
    parsed = json.loads(unfucked)
    return parsed


def find_archives(archives="twiter-archives") -> typing.List[str]:
    """Find archives saved locally.

    Assumes archives are saved to ./twitter-archives in the root of a Hugo blog repo.
    (No better place for them, really;
    they include private data like DMs which should not be exposed
    and therefore they cannot go into static/,
    and Hugo's ./data only supports json/toml/etc,
    which will not work with the images saved as separate files in the Twitter archives.)
    """

    archives = []
    for item in os.listdir(archives):
        archive = TwitterArchive.frompath(os.path.join(archives, item))
        if not os.path.exists(archive.profilejs) or not os.path.exists(archive.tweetjs):
            logger.debug(f"Skipping item {item} as it is not a complete archive")
            continue
        archives.append(archive)
    return archives


def archive2data(
    archive: TwitterArchive,
    api: typing.Optional[tweepy.API] = None,
    max_recurse=1,
    api_force_download=False,
    hugodata="data",
):
    """Parse all the tweets in an archive and return a list of InflatedTweet objects"""

    os.makedirs(f"{hugodata}/twarchive", exist_ok=True)

    parsed_account = parse_twitter_window_YTD_bullshit(archive.accountjs)
    account = parsed_account[0]["account"]
    username = account["username"]
    accountid = account["accountId"]
    displayname = account["accountDisplayName"]

    parsed_profile = parse_twitter_window_YTD_bullshit(archive.profilejs)
    profile = parsed_profile[0]["profile"]
    pfp_url_filename = profile["avatarMediaUrl"].split("/")[-1]
    pfp_filename = f"{accountid}-{pfp_url_filename}"
    pfp_path = os.path.join(archive.profilemedia, pfp_filename)
    with open(pfp_path, "br") as pfpfp:
        pfp_bytes = pfpfp.read()

    parsed_tweets = parse_twitter_window_YTD_bullshit(archive.tweetjs)

    infltweets: typing.List[InflatedTweet] = []
    for outertweet in parsed_tweets:
        tweet = outertweet["tweet"]
        tweetid = tweet["id_str"]
        logprefix = f"Tweet {tweetid} in archive {archive.path}"
        if twitter_archive_tweet_is_low_fidelity_retweet(tweet):
            if api:
                logger.info(
                    f"{logprefix} is a low fidelity retweet, will try to download the original from Twitter..."
                )
                twitterapi.tweet2data_continue_on_error(
                    api,
                    tweetid,
                    None,
                    force=api_force_download,
                    max_rlevel=max_recurse,
                )
            else:
                logger.info(
                    f"{logprefix} is low fidelity retweet and api argument was not passed, skipping..."
                )
        else:
            logger.info(f"{logprefix} is a regular tweet, saving to disk...")
            infltweet = inflated_tweet_from_twitter_archive(
                tweet,
                pfp_bytes,
                username,
                displayname,
                archive,
            )
            filename = f"{hugodata}/twarchive/{tweetid}.json"
            with open(filename, "w") as fp:
                json.dump(infltweet, fp, cls=InflatedTweetEncoder, indent=2)
            infltweets.append(infltweet)
