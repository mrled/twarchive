"""Code related to making the tweet body"""

import typing

from twarchive import util
from twarchive.inflatedtweet.inflatedtweet import Replacement


def tweet_html_body(
    tweet_text: str,
    entities: typing.Dict,
    render_qt_link=False,
) -> str:
    """Create an HTML tweet body for archiving

    - Text hashtags become links to search Twitter for the hashtag
    - Text URLs become links to the original URL (not the shortened one)
    - Text @mentions become links to the user's profile on Twitter
    - Text links to media get stripped out complete (they will be handled elsewhere)

    Arguments:
        tweet_text:     The full_text of a tweet
        entities:       A tweepy.Tweet.entities or a tweet['entities'] from a tweet in a Twitter archive
        render_qt_link: If one of the URLs is a link to another tweet,
                        should it be rendered as a link?
                        If False, links to tweets will be stripped out completely,
                        so they can be included in full fidelity by other means.
                        If True, links to tweets will be rendered as regular <a> links.
    """
    replacements = {}
    for hashtag in entities.get("hashtags", []):
        hash = hashtag["text"]
        start, end = hashtag["indices"]
        replace = f'<a href="https://twitter.com/hashtag/{hash}">#{hash}</a>'
        replacements[start] = Replacement(int(start), int(end), replace)
    for url in entities.get("urls", []):
        expanded_url = url["expanded_url"]
        display_url = url["display_url"]
        start, end = url["indices"]
        if util.uri_is_tweet(expanded_url) and not render_qt_link:
            replace = ""
        else:
            replace = f'<a href="{expanded_url}">{display_url}</a>'
        replacements[start] = Replacement(int(start), int(end), replace)
    for mention in entities.get("user_mentions", []):
        start, end = mention["indices"]
        username = mention["screen_name"]
        replace = f'<a href="https://twitter.com/{username}">@{username}</a>'
        replacements[start] = Replacement(int(start), int(end), replace)
    for media in entities.get("media", []):
        start, end = media["indices"]
        replacements[start] = Replacement(int(start), int(end), "")

    # Iterate through replacements in reverse
    # Means all the indexes will stay correct
    for key in sorted(replacements.keys(), reverse=True):
        r = replacements[key]
        pre = tweet_text[0 : r.start]
        post = tweet_text[r.end : len(tweet_text)]
        tweet_text = pre + r.replace + post

    # Clients may insert newlines, but we have to convert them to <br/> or else it won't display them properly
    tweet_text = tweet_text.replace("\n", "<br/>")

    return tweet_text
