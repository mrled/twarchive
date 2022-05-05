"""Functions that relate to a Hugo blog"""

import datetime
import json
import os
import re
import subprocess
import textwrap
import typing


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
        "\{\{. twarchiveThread .[0-9]+(-intentionallyinvalid)?",
        content,
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


def get_downloaded_tweets(twarchive="./data/twarchive") -> typing.List[str]:
    """Return a list of tweet IDs that have already been downloaded"""
    return [t.strip(".json") for t in os.listdir("data/twarchive")]


def showinlines():
    inlines = find_inline_tweets()
    print("Note: these tweets may QT other tweets, which are not listed here")
    for line in inlines:
        print(f"- {line}")


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
