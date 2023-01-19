"""Functionality related to a downloaded Twitter archive

Twitter allows account owners to download all their own tweets,
as well as a bunch of other data,
in an archive file.
We can use any archive files as a definitive copy of a tweet.

Note that a tweet found in an archive should _never_ be redownloaded,
at least as long as Twitter does not permit edits.
"""

import datetime
from functools import cache
import functools
import json
import os
import re
import typing

import tweepy

from twarchive import hugo, logger, twitterapi
from twarchive.inflatedtweet.from_twitter_archive import (
    inflated_tweet_from_twitter_archive,
    twitter_archive_tweet_is_low_fidelity_retweet,
)
from twarchive.inflatedtweet.inflatedtweet import InflatedTweet


class TwitterArchive(typing.NamedTuple):
    """An on-disk, extracted Twitter archive

    Note: NamedTuple objects cannot be annotated as @functools.cached_property
    Instead, they can use stacked @property, @functools.cache decorators.
    <https://docs.python.org/dev/library/functools.html#functools.cached_property>
    """

    path: str
    manifestjs: str
    profilejs: str
    tweetjs: str
    accountjs: str
    profilemedia: str
    tweetmedia: str

    def anymissing(self) -> typing.List[str]:
        """Checks for existence of required files"""
        required = [
            self.manifestjs,
            self.profilejs,
            self.tweetjs,
            self.accountjs,
            self.profilemedia,
            self.tweetmedia,
        ]
        missing = [i for i in required if not os.path.exists(i)]
        return missing

    @property
    @functools.cache
    def manifest(self) -> typing.Dict:
        parsed_manifest = parse_twitter_manifest_js(self.manifestjs)
        return parsed_manifest

    @property
    @functools.cache
    def generation_date(self) -> datetime.datetime:
        gendate_str = self.manifest["archiveInfo"]["generationDate"]
        # eg: "generationDate" : "2022-05-06T17:27:17.889Z"
        # gendate_dt = datetime.datetime.fromisoformat(gendate_str)
        gendate_dt = datetime.datetime.strptime(gendate_str, r"%Y-%m-%dT%H:%M:%S.%fz")
        return gendate_dt

    @classmethod
    def frompath(cls, p: str) -> "TwitterArchive":
        data = os.path.join(p, "data")
        archive = cls(
            p,
            os.path.join(data, "manifest.js"),
            os.path.join(data, "profile.js"),
            os.path.join(data, "tweet.js"),
            os.path.join(data, "account.js"),
            os.path.join(data, "profile_media"),
            os.path.join(data, "tweet_media"),
        )
        return archive


def parse_twitter_manifest_js(manifest: str) -> typing.Dict:
    """The fucking Twitter archive MANIFEST is in a DIFFERENT fucking deranged format for no good reason"""
    with open(manifest) as mfp:
        contents = mfp.read()
    unfucked = re.sub(r"^window\.__THAR_CONFIG = ", "", contents)
    parsed = json.loads(unfucked)
    return parsed


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


def find_archives(site: hugo.HugoSite) -> typing.List[str]:
    """Find archives saved locally.

    Assumes archives are saved to ./twitter-archives in the root of a Hugo blog repo.
    (No better place for them, really;
    they include private data like DMs which should not be exposed
    and therefore they cannot go into static/,
    and Hugo's ./data only supports json/toml/etc,
    which will not work with the images saved as separate files in the Twitter archives.)
    """

    archives = []
    for archive in os.listdir(site.twitter_archives):
        archive = TwitterArchive.frompath(os.path.join(site.twitter_archives, archive))
        missing = archive.anymissing()
        if missing:
            logger.debug(
                f"Skipping archive {archive} as it is not a complete archive, missing: {missing}"
            )
            continue
        archives.append(archive)
    return archives


def archive2data(
    site: hugo.HugoSite,
    archive: TwitterArchive,
    api: typing.Optional[tweepy.API] = None,
    max_recurse=1,
    api_force_download=False,
):
    """Parse all the tweets in an archive and return a list of InflatedTweet objects"""

    os.makedirs(site.data_twarchive, exist_ok=True)

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
                    site,
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
            filename = os.path.join(site.data_twarchive, f"{tweetid}.json")
            infltweet.jdump(filepath=filename)
            infltweets.append(infltweet)
