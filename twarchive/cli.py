import argparse
import pdb
import sys
import traceback
import typing

from twarchive import implementation, version


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

    sub_version = subparsers.add_parser("version", help="Show program version")

    sub_tweet2json = subparsers.add_parser(
        "tweet2json",
        parents=[twitter_opts],
        help="Download JSON for a tweet, including image data",
    )
    sub_tweet2json.add_argument("tweetid", help="ID of a tweet to download")
    sub_tweet2json.add_argument("filename", help="Path to save JSON to")

    sub_tweet2data = subparsers.add_parser(
        "tweet2data",
        parents=[twitter_opts],
        help="Download JSON for a tweet, and store it under './data/twarchive/$tweetId.json', including any QTs or parents",
    )
    sub_tweet2data.add_argument("tweetid", help="ID of a tweet to download")

    sub_showinlines = subparsers.add_parser(
        "showinlines", help="Show tweets inlined with the 'twarchiveTweet' shortcode"
    )

    sub_inline2data = subparsers.add_parser(
        "inline2data",
        parents=[twitter_opts],
        help="Download JSON for all tweets that are inlined via the 'twarchiveTweet' shortcode.",
    )

    sub_data2md = subparsers.add_parser(
        "data2md",
        help="Create a page under content/twarchive/ for every downloaded tweet",
    )

    sub_examine = subparsers.add_parser(
        "examine",
        parents=[twitter_opts],
        help="Get the response from Twitter and launch the debugger",
    )
    sub_examine.add_argument("tweetid", help="ID of the tweet to examine")

    sub_user2data = subparsers.add_parser(
        "user2data",
        parents=[twitter_opts],
        help="Retrieve a user's full timeline from Twitter and store in site data",
    )
    sub_user2data.add_argument("username", help="Twitter username")
    sub_user2data.add_argument(
        "--retrieve-all",
        action="store_true",
        help="Keep retrieving tweets from this user even if we retrieve a tweet we already have. Has no effect if --force is True, but if --force is False, it will download older tweets without redownloading media/QTs from newer ones it already has.",
    )

    parsed = parser.parse_args()
    return parser, parsed


def main():
    """Main program"""
    parser, parsed = parseargs()
    if parsed.debug:
        sys.excepthook = idb_excepthook

    if parsed.action == "version":
        print(f"{parser.prog} version {version.__version__}")
        return 0
    elif parsed.action == "tweet2json":
        api = implementation.authenticate(parsed.consumer_key, parsed.consumer_secret)
        implementation.tweetid2json(api, parsed.tweetid, parsed.filename)
    elif parsed.action == "tweet2data":
        api = implementation.authenticate(parsed.consumer_key, parsed.consumer_secret)
        implementation.tweet2data(
            api,
            tweetid=parsed.tweetid,
            force=parsed.force,
            max_rlevel=parsed.max_recurse,
        )
        implementation.data2md()
    elif parsed.action == "showinlines":
        implementation.showinlines()
    elif parsed.action == "inline2data":
        implementation.inline2data(
            parsed.consumer_key,
            parsed.consumer_secret,
            force=parsed.force,
            max_rlevel=parsed.max_recurse,
        )
        implementation.data2md()
    elif parsed.action == "data2md":
        implementation.data2md()
    elif parsed.action == "examine":
        api = implementation.authenticate(parsed.consumer_key, parsed.consumer_secret)
        tweet = implementation.get_status_expanded(api, parsed.tweetid)
        pdb.set_trace()
    elif parsed.action == "user2data":
        api = implementation.authenticate(parsed.consumer_key, parsed.consumer_secret)
        implementation.usertweets2data(
            api,
            parsed.username,
            max_rlevel=parsed.max_recurse,
            force=parsed.force,
            retrieve_all=parsed.retrieve_all,
        )
        implementation.data2md()
    else:
        raise Exception(f"Unknown action: {parsed.action}")
