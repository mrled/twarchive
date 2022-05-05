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
import tempfile
import typing

from twarchive import logger


class TwitterArchive(typing.NamedTuple):
    """An on-disk, extracted Twitter archive"""

    profilejs: str
    tweetjs: str
    profilemedia: str
    tweetmedia: str

    def frompath(p: str) -> "TwitterArchive":
        archive = TwitterArchive(
            os.path.join(p, "data/profile.js"),
            os.path.join(p, "data/tweet.js"),
            os.path.join(p, "data/profile_media"),
            os.path.join(p, "data/tweet_media"),
        )
        return archive


def parse_twitter_window_YTD_bullshit(archivefile: str) -> typing.Dict:
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


def archive2data(archive: TwitterArchive, hugodata="data"):
    """Parse all the tweets in an archive and save them as individual files to Hugo"""

    with open(archive.profilejs) as pfp:
        parsed_profile = json.load(pfp)
    profile = parsed_profile["window.YTD.profile.part0"][0]["profile"]

    with open(archive.tweetjs) as tfp:
        parsed_tweets = json.load(tfp)
    tweets = parsed_tweets["window.YTD.tweet.part0"]

    for tweet in tweets:
        print(tweet.full_text)
