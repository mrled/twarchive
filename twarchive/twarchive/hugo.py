"""Functions that relate to a Hugo blog"""

import datetime
import json
import os
import pathlib
import re
import subprocess
import textwrap
import typing


class HugoSite:
    def __init__(self, base: str):
        self.base = pathlib.Path(base)
        self.content = os.path.join(self.base, "content")
        self.content_twarchive = os.path.join(self.content, "twarchive")
        self.data = os.path.join(self.base, "data")
        self.data_twarchive = os.path.join(self.data, "twarchive")
        self.twitter_archives = os.path.join(self.base, "twitter-archives")


def find_inline_tweets(site: HugoSite) -> typing.List[str]:
    """Find tweets inlined with 'twarchiveTweet' or 'twarchiveThread' shortcodes in site content"""

    result = []

    rgcmd = [
        "rg",
        "--no-filename",
        "--no-line-number",
        r"\{\{. twarchiveTweet .[0-9]+(-intentionallyinvalid)?",
        site.content,
    ]
    rg = subprocess.run(rgcmd, capture_output=True)
    outlines = rg.stdout.decode().strip().split("\n")
    for line in outlines:
        if not line:
            continue
        m = re.search(
            "{{. twarchiveTweet .(?P<tweetid>[0-9]+(:?-intentionallyinvalid)?)", line
        )
        result += [m["tweetid"]]

    rgcmd = [
        "rg",
        "--no-filename",
        "--no-line-number",
        r"\{\{. twarchiveThread .[0-9]+(-intentionallyinvalid)?",
        site.content,
    ]
    rg = subprocess.run(rgcmd, capture_output=True)
    outlines = rg.stdout.decode().strip().split("\n")
    for line in outlines:
        if not line:
            continue
        m = re.search(
            "{{. twarchiveThread .(?P<tweetid>[0-9]+(:?-intentionallyinvalid)?)", line
        )
        result += [m["tweetid"]]

    return set(result)


def get_downloaded_tweets(site: HugoSite) -> typing.List[str]:
    """Return a list of tweet IDs that have already been downloaded"""
    return [t.strip(".json") for t in os.listdir(site.data_twarchive)]


def showinlines(site: HugoSite):
    inlines = find_inline_tweets(site)
    print("Note: these tweets may QT other tweets, which are not listed here")
    for line in inlines:
        print(f"- {line}")


def data2md(site: HugoSite):
    """For tweets that have been downloaded to the data directory, make a page for them in the content"""
    os.makedirs(site.content_twarchive, exist_ok=True)
    for tweet_json in os.listdir(site.data_twarchive):
        tweet_json_path = os.path.join(site.data_twarchive, tweet_json)
        with open(tweet_json_path) as tjfp:
            tweet = json.load(tjfp)
        tweet_date = datetime.datetime.strptime(tweet["date"], "%Y-%m-%dT%H:%M:%S%z")
        tweetid = tweet_json.strip(".json")
        tweet_md_path = os.path.join(site.content_twarchive, f"{tweetid}.md")
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
