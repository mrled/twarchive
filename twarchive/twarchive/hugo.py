"""Functions that relate to a Hugo blog"""

import datetime
import json
import os
import pathlib
import re
import string
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

    tweets = {}
    tweetgraph = {}

    # Load all tweets into RAM so that we only have to read from the filesystem once.
    # For reference, my archive of 2700 tweets is 323MB on disk and takes about 2-3 seconds to load.
    tweet_file_list = os.listdir(site.data_twarchive)
    for idx, tweet_json in enumerate(tweet_file_list):
        if idx % 100 == 0:
            print(f"Loading tweet {idx} of {len(tweet_file_list)}")
        tweet_json_path = os.path.join(site.data_twarchive, tweet_json)
        with open(tweet_json_path) as tjfp:
            tweet = json.load(tjfp)
        tweetid = tweet_json.strip(".json")
        tweets[tweetid] = tweet

        if tweet.get("replyto_tweetid"):
            tweetgraph[tweetid] = tweet["replyto_tweetid"]

    parents = list(set(tweetgraph.values()))
    thread_finals = [t for t in tweetgraph.keys() if t not in parents]

    # Find the end of every reply chain.
    for childid in tweetgraph:
        if childid not in parents:
            thread_finals += [childid]

    # For the ends of reply chains, we'll add content with the whole thread.
    thread_addemdum_template = string.Template(
        "\n".join(
            [
                "",
                "This tweet is part of a thread:",
                "",
                r"""{{% twarchiveThread "$tweetid" %}}""",
                "",
            ]
        )
    )

    os.makedirs(site.content_twarchive, exist_ok=True)
    for tweetid, tweet in tweets.items():
        tweet_md_path = os.path.join(site.content_twarchive, f"{tweetid}.md")
        tweet_date = datetime.datetime.strptime(tweet["date"], "%Y-%m-%dT%H:%M:%S%z")
        mdcontents = textwrap.dedent(
            f"""\
            ---
            tweetid: "{tweetid}"
            date: {tweet_date}
            ---
            """
        )

        if tweetid in thread_finals:
            mdcontents += (
                "\n\n" + thread_addemdum_template.substitute(tweetid=tweetid) + "\n"
            )

        with open(tweet_md_path, "w") as tmdfp:
            tmdfp.write(mdcontents)
