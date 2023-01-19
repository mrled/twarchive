import argparse
import os
import pdb
import sys
import traceback
import typing

import tweepy

from twarchive import hugo
from twarchive import logger
from twarchive import twitterapi
from twarchive import twitterarchive
from twarchive import version
from twarchive.inflatedtweet.inflatedtweet import InflatedTweet


def idb_excepthook(type, value, tb):
    """Call an interactive debugger in post-mortem mode

    If you do "sys.excepthook = idb_excepthook", then an interactive debugger
    will be spawned at an unhandled exception
    """
    if hasattr(sys, "ps1") or not sys.stderr.isatty():
        sys.__excepthook__(type, value, tb)
    else:
        traceback.print_exception(type, value, tb)
        print
        pdb.pm()


def inline2data(
    site: hugo.HugoSite, api: tweepy.API, max_rlevel: int, force: bool = False
):
    """Save tweets to data that have been inlined

    Does not redownload items already saved.
    """
    for tweetid in hugo.find_inline_tweets(site):
        if tweetid.endswith("-intentionallyinvalid"):
            logger.info(f"Skipping intentionally invalid tweet id {tweetid}")
        else:
            twitterapi.tweet2data(
                site, api, tweetid=tweetid, force=force, max_rlevel=max_rlevel
            )


def list_directory_tweetid_filename(directory: str) -> typing.List[str]:
    """List a directory of files with tweetid filenames and return them sorted.

    When sorting, zero pad all tweet IDs.

    Filenames that do not start with numbers are ignored.
    """

    def sortkey(s: str):
        return int(s.split(".")[0])

    children = os.listdir(directory)
    child_numbers = [c for c in children if c[0].isdigit()]
    child_numbers.sort(key=sortkey)
    return child_numbers


def parseargs():
    """Parse program arguments"""
    parser = argparse.ArgumentParser(description="Manage tweets")
    subparsers = parser.add_subparsers(dest="action", required=True)
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Launch a debugger on unhandled exception",
    )

    ## Options related to the Twitter API
    twitter_opts = argparse.ArgumentParser(add_help=False)
    # Defaults are official keys for iOS app
    # https://gist.github.com/shobotch/5160017
    twitter_opts.add_argument(
        "--consumer-key", default="IQKbtAYlXLripLGPWd0HUA", help="Twitter consumer key"
    )
    twitter_opts.add_argument(
        "--consumer-secret",
        default="GgDYlkSvaPxGxC4X8liwpUoqKwwr3lCADbz8A7ADU",
        help="Twitter consumer secret",
    )
    twitter_opts.add_argument(
        "--max-recurse",
        type=int,
        default=20,
        help="How many parent/QT tweets should we find",
    )
    twitter_opts.add_argument(
        "--force",
        action="store_true",
        help="Redownload data that has already been downloaded",
    )

    ## Options related to a Hugo site
    hugo_opts = argparse.ArgumentParser(add_help=False)
    hugo_opts.add_argument(
        "--hugo-site-base",
        default=".",
        help="Path to a Hugo site. Defaults to the $PWD.",
    )

    ## Subcommand: version
    sub_version = subparsers.add_parser("version", help="Show program version")
    sub_version.add_argument(
        "--quiet",
        action="store_true",
        help="Show just the version (used in development)",
    )

    ## Subcommand: ls
    sub_ls = subparsers.add_parser(
        "ls",
        parents=[hugo_opts],
        help="List tweet files in a Hugo repository, sorted by tweet ID and accounting for tweet IDs of different lengths",
    )
    sub_ls.add_argument(
        "directory",
        choices=["data", "content"],
        help="Choose the directory to list - either data/twarchive or content/twarchive",
    )

    ## Subcommand: internals
    sub_internals = subparsers.add_parser(
        "internals", help="Internal commands used in development"
    )
    sub_internals_subparsers = sub_internals.add_subparsers(
        dest="internalsaction", required=True
    )

    ## Subcommand: internals: Subcommand: examine
    sub_internals_sub_examine = sub_internals_subparsers.add_parser(
        "examine",
        parents=[twitter_opts],
        help="Get the response from Twitter and launch the debugger",
    )
    sub_internals_sub_examine.add_argument("tweetid", help="ID of the tweet to examine")

    ## Subcommand: internals: Subcommand: json-load-dump-tweets
    # Useful for testing our en/de-coders
    # Also nice to ensure that all tweets were saved with indent=2 and sort_keys=True,
    # which is useful when saving the resulting JSON to git for diffing etc
    sub_internals_sub_json_load_dump_tweets = sub_internals_subparsers.add_parser(
        "json-load-dump-tweets",
        parents=[hugo_opts],
        help="Use our custom JSON en/de-coders to parse JSON of every tweet saved to data/twarchive/*.json, and save it back out.",
    )

    ## Subcommand: tweet2json
    sub_tweet2json = subparsers.add_parser(
        "tweet2json",
        parents=[twitter_opts, hugo_opts],
        help="Download JSON for a tweet, including image data",
    )
    sub_tweet2json.add_argument("tweetid", help="ID of a tweet to download")
    sub_tweet2json.add_argument("filename", help="Path to save JSON to")

    ## Subcommand: tweet2data
    sub_tweet2data = subparsers.add_parser(
        "tweet2data",
        parents=[twitter_opts, hugo_opts],
        help="Download JSON for a tweet, and store it under './data/twarchive/$tweetId.json', including any QTs or parents",
    )
    sub_tweet2data.add_argument("tweetid", help="ID of a tweet to download")

    ## Subcommand: showinlines
    sub_showinlines = subparsers.add_parser(
        "showinlines",
        parents=[hugo_opts],
        help="Show tweets inlined with the 'twarchiveTweet' shortcode",
    )

    ## Subcommand: inline2data
    sub_inline2data = subparsers.add_parser(
        "inline2data",
        parents=[twitter_opts, hugo_opts],
        help="Download JSON for all tweets that are inlined via the 'twarchiveTweet' shortcode.",
    )

    ## Subcommand: data2md
    sub_data2md = subparsers.add_parser(
        "data2md",
        parents=[hugo_opts],
        help="Create a page under content/twarchive/ for every downloaded tweet",
    )

    ## Subcommand: user2data
    sub_user2data = subparsers.add_parser(
        "user2data",
        parents=[twitter_opts, hugo_opts],
        help="Retrieve a user's full timeline from Twitter and store in site data",
    )
    sub_user2data.add_argument("username", help="Twitter username")
    sub_user2data.add_argument(
        "--retrieve-all",
        action="store_true",
        help="Keep retrieving tweets from this user even if we retrieve a tweet we already have. Has no effect if --force is True, but if --force is False, it will download older tweets without redownloading media/QTs from newer ones it already has.",
    )

    ## Subcommand: archive2data
    sub_archive2data = subparsers.add_parser(
        "archive2data",
        parents=[twitter_opts, hugo_opts],
        help="Parse a Twitter archive extracted to twitter-archives/<name> and save the result to the Hugo data dir",
    )
    sub_archive2data.add_argument(
        "--archive",
        help="Name of the archive to parse; if not present, find archives automatically under ./twitter-archives",
    )
    sub_archive2data.add_argument(
        "--no-api",
        action="store_true",
        help="Don't query the API for missing RTs, QTs, or thread parents",
    )

    ## Subcommand: show-inline-tweets
    sub_show_inline_tweets = subparsers.add_parser(
        "show-inline-tweets",
        parents=[hugo_opts],
        help="Show a list of all tweets included by twarchive Hugo partials",
    )

    ## Done
    parsed = parser.parse_args()
    return parser, parsed


def main():
    """Main program"""
    parser, parsed = parseargs()
    if parsed.debug:
        sys.excepthook = idb_excepthook

    if parsed.action == "version":
        if parsed.quiet:
            print(version.__version__)
        else:
            print(f"{parser.prog} version {version.__version__}")
        return 0

    elif parsed.action == "ls":
        site = hugo.HugoSite(parsed.hugo_site_base)
        if parsed.directory == "data":
            dir = site.data_twarchive
        elif parsed.directory == "content":
            dir = site.content_twarchive
        else:
            raise Exception(f"Unknown directory {parsed.directory}")
        children = [os.path.join(dir, c) for c in list_directory_tweetid_filename(dir)]
        print("\n".join(children))

    elif parsed.action == "internals":
        if parsed.internalsaction == "examine":
            api = twitterapi.authenticate(parsed.consumer_key, parsed.consumer_secret)
            tweet = twitterapi.get_status_expanded(api, parsed.tweetid)
            pdb.set_trace()
        elif parsed.internalsaction == "json-load-dump-tweets":
            site = hugo.HugoSite(parsed.hugo_site_base)
            for tweetjson in os.listdir(site.data_twarchive):
                tweetjson_path = os.path.join(site.data_twarchive, tweetjson)
                with open(tweetjson_path) as tjfp:
                    infltweet = InflatedTweet.jload(tjfp)
                with open(tweetjson_path, "w") as tjfp:
                    infltweet.jdump(tjfp)

    elif parsed.action == "tweet2json":
        api = twitterapi.authenticate(parsed.consumer_key, parsed.consumer_secret)
        twitterapi.tweetid2json(api, parsed.tweetid, parsed.filename)

    elif parsed.action == "tweet2data":
        site = hugo.HugoSite(parsed.hugo_site_base)
        api = twitterapi.authenticate(parsed.consumer_key, parsed.consumer_secret)
        twitterapi.tweet2data(
            site,
            api,
            tweetid=parsed.tweetid,
            force=parsed.force,
            max_rlevel=parsed.max_recurse,
        )
        hugo.data2md(site)

    elif parsed.action == "showinlines":
        site = hugo.HugoSite(parsed.hugo_site_base)
        hugo.showinlines(site)

    elif parsed.action == "inline2data":
        site = hugo.HugoSite(parsed.hugo_site_base)
        api = twitterapi.authenticate(parsed.consumer_key, parsed.consumer_secret)
        twitterapi.inline2data(
            site,
            api,
            force=parsed.force,
            max_rlevel=parsed.max_recurse,
        )
        hugo.data2md(site)

    elif parsed.action == "data2md":
        site = hugo.HugoSite(parsed.hugo_site_base)
        hugo.data2md(site)

    elif parsed.action == "user2data":
        site = hugo.HugoSite(parsed.hugo_site_base)
        api = twitterapi.authenticate(parsed.consumer_key, parsed.consumer_secret)
        twitterapi.usertweets2data(
            site,
            api,
            parsed.username,
            max_rlevel=parsed.max_recurse,
            force=parsed.force,
            retrieve_all=parsed.retrieve_all,
        )
        hugo.data2md(site)

    elif parsed.action == "archive2data":
        site = hugo.HugoSite(parsed.hugo_site_base)

        if parsed.archive:
            archives = [
                twitterarchive.TwitterArchive.frompath(
                    os.path.join(site.twitter_archives, parsed.archive)
                )
            ]
        else:
            archives = twitterarchive.find_archives(site)

        if parsed.no_api:
            api = None
        else:
            api = twitterapi.authenticate(parsed.consumer_key, parsed.consumer_secret)

        for archive in archives:
            twitterarchive.archive2data(
                site,
                archive,
                api=api,
                max_recurse=parsed.max_recurse,
                api_force_download=parsed.force,
            )

    elif parsed.action == "show-inline-tweets":
        site = hugo.HugoSite(parsed.hugo_site_base)
        for inline in hugo.find_inline_tweets(site):
            print(inline)

    else:
        raise Exception(f"Unknown action: {parsed.action}")
