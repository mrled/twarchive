import base64
import datetime
import json
import os
import re
import subprocess
import textwrap
import typing

import requests
import tweepy

from twarchive import logger


def uri_is_tweet(uri: str) -> bool:
    """Return whether a URI points to a single tweet"""
    return bool(re.match("https\:\/\/twitter\.com\/.*\/status\/[0-9]+", uri))


def tweeturi2tweetid(uri: str) -> str:
    """Given a tweet URI, return just the tweet ID it contains"""
    m = re.match("https\:\/\/twitter\.com\/.*\/status\/(?P<tweetid>[0-9]+)", uri)
    return m["tweetid"]


class Replacement(typing.NamedTuple):
    """Text replacement for a tweet body."""

    start: int
    end: int
    replace: str


class TweetMediaAttachment:
    """A single media item like a photo"""

    def __init__(
        self,
        media_type: str,
        content_type: str,
        width: int,
        height: int,
        alttext: str,
        url: str,
        data: bytes,
    ):
        if media_type not in ["photo", "video", "animated_gif"]:
            raise ValueError(f"Unknown media_type {media_type}")
        self.media_type = media_type
        self.content_type = content_type
        self.width = width
        self.height = height
        self.alttext = alttext
        self.url = url
        if isinstance(data, str):
            self.data = base64.b64decode(data)
        else:
            self.data = data


def tweet_html_body(
    tweet: tweepy.models.Status,
    render_qt_link=False,
) -> str:
    """Create an HTML tweet body from the Tweepy object for a single tweet.

    - Text hashtags become links to search Twitter for the hashtag
    - Text URLs become links to the original URL (not the shortened one)
    - Text @mentions become links to the user's profile on Twitter
    - Text links to media get stripped out complete (they will be handled elsewhere)

    Arguments:
        tweet:          A Tweepy object representing a single tweet
        render_qt_link: If one of the URLs is a link to another tweet,
                        should it be rendered as a link?
                        If False, links to tweets will be stripped out completely,
                        so they can be included in full fidelity by other means.
                        If True, links to tweets will be rendered as regular <a> links.
    """
    replacements = {}
    for hashtag in tweet.entities.get("hashtags", []):
        hash = hashtag["text"]
        start, end = hashtag["indices"]
        replace = f'<a href="https://twitter.com/hashtag/{hash}">#{hash}</a>'
        replacements[start] = Replacement(start, end, replace)
    for url in tweet.entities.get("urls", []):
        expanded_url = url["expanded_url"]
        display_url = url["display_url"]
        start, end = url["indices"]
        if uri_is_tweet(expanded_url) and not render_qt_link:
            replace = ""
        else:
            replace = f'<a href="{expanded_url}">{display_url}</a>'
        replacements[start] = Replacement(start, end, replace)
    for mention in tweet.entities.get("user_mentions", []):
        start, end = mention["indices"]
        username = mention["screen_name"]
        replace = f'<a href="https://twitter.com/{username}">@{username}</a>'
        replacements[start] = Replacement(start, end, replace)
    for media in tweet.entities.get("media", []):
        start, end = media["indices"]
        replacements[start] = Replacement(start, end, "")

    htmlbody = tweet.full_text

    # Iterate through replacements in reverse
    # Means all the indexes will stay correct
    for key in sorted(replacements.keys(), reverse=True):
        r = replacements[key]
        pre = htmlbody[0 : r.start]
        post = htmlbody[r.end : len(htmlbody)]
        htmlbody = pre + r.replace + post

    # Clients may insert newlines, but we have to convert them to <br/> or else it won't display them properly
    htmlbody = htmlbody.replace("\n", "<br/>")

    return htmlbody


def guess_mime_type(filename: str) -> str:
    """Given a filename, guess its MIME type. Works with URIs as well."""
    # This is just a random list I found, lol
    mime_types = dict(
        # images
        png="image/png",
        jpe="image/jpeg",
        jpeg="image/jpeg",
        jpg="image/jpeg",
        gif="image/gif",
        bmp="image/bmp",
        ico="image/vnd.microsoft.icon",
        tiff="image/tiff",
        tif="image/tiff",
        svg="image/svg+xml",
        svgz="image/svg+xml",
        # video
        mp4="video/mp4",
        qt="video/quicktime",
        mov="video/quicktime",
        # audio
        mp3="audio/mpeg",
        ogg="audio/ogg",
    )

    extension = os.path.splitext(filename)[1][1:].lower()

    # Some Twitter media URIs have a query string at the end, like
    # <https://video.twimg.com/ext_tw_video/1221557894694559750/pu/vid/320x568/Vnzq6WB09j9CMLOc.mp4?tag=10>

    extension = re.sub("\?.*", "", extension)

    return mime_types[extension]


class InflatedTweet:
    """A tweet with all supplemental data (like images) also downloaded"""

    def __init__(
        self,
        id: str,
        date: datetime.datetime,
        date_original_format: str,
        full_text: str,
        full_html_strip_qts: str,
        full_html_link_qts: str,
        media: typing.List[TweetMediaAttachment],
        entities: typing.Any,
        qts: typing.List[str],
        rt_of: str,
        thread_parent_id: str,
        username: str,
        user_displayname: str,
        user_pfp: bytes,
        retrieved_date: datetime.datetime,
    ):
        self.id = id

        if isinstance(date, str):
            self.date = datetime.datetime.fromisoformat(date)
        else:
            self.date = date

        self.date_original_format = date_original_format
        self.full_text = full_text
        self.full_html_strip_qts = full_html_strip_qts
        self.full_html_link_qts = full_html_link_qts
        self.media = media
        self.entities = entities
        self.qts = qts
        self.rt_of = rt_of
        self.thread_parent_id = thread_parent_id
        self.username = username
        self.user_displayname = user_displayname

        if isinstance(user_pfp, str):
            self.user_pfp = base64.b64decode(user_pfp)
        else:
            self.user_pfp = user_pfp

        self.retrieved_date = retrieved_date

    @classmethod
    def from_tweet(cls, tweet: tweepy.models.Status):
        qts: typing.List[str] = []
        media: typing.List[TweetMediaAttachment] = []

        try:
            entities = tweet.entities
        except AttributeError:
            entities = {}
        for item in entities.get("urls"):
            if uri_is_tweet(item["expanded_url"]):
                qtid = tweeturi2tweetid(item["expanded_url"])
                qts += [qtid]

        try:
            extended_entities = tweet.extended_entities
        except AttributeError:
            extended_entities = {}
        for item in extended_entities.get("media", []):

            if item["type"] == "photo":
                w = item["sizes"]["small"]["w"]
                h = item["sizes"]["small"]["h"]
                alttext = item.get("media_alt_text", "")
                url = item["media_url_https"]
                mime = item.get("content_type", guess_mime_type(url))
                data = requests.get(url).content
                attachment = TweetMediaAttachment(
                    "photo", mime, w, h, alttext, url, data
                )
                media += [attachment]

            elif item["type"] == "video":
                w = item["sizes"]["small"]["w"]
                h = item["sizes"]["small"]["h"]
                alttext = item.get("media_alt_text", "")
                variants = {
                    int(v["bitrate"]): v
                    for v in item["video_info"]["variants"]
                    if "bitrate" in v
                }
                best_bitrate = max(variants.keys())
                variant = variants[best_bitrate]
                url = variant["url"]
                mime = variant.get("content_type", guess_mime_type(url))
                data = requests.get(url).content
                attachment = TweetMediaAttachment(
                    "video", mime, w, h, alttext, url, data
                )
                media += [attachment]

            elif item["type"] == "animated_gif":
                w = item["sizes"]["small"]["w"]
                h = item["sizes"]["small"]["h"]
                alttext = item.get("media_alt_text", "")
                variants = {
                    int(v["bitrate"]): v
                    for v in item["video_info"]["variants"]
                    if "bitrate" in v
                }
                best_bitrate = max(variants.keys())
                variant = variants[best_bitrate]
                url = variant["url"]
                mime = variant.get("content_type", guess_mime_type(url))
                data = requests.get(url).content
                attachment = TweetMediaAttachment(
                    "animated_gif", mime, w, h, alttext, url, data
                )
                media += [attachment]

            else:
                raise Exception(
                    f"Unknown item type {item['type']} trying to download media for tweet {tweet.id}"
                )

        try:
            rt_of = tweet.retweeted_status.id_str
        except AttributeError:
            rt_of = None

        user_pfp = requests.get(tweet.user.profile_image_url).content

        infltweet = cls(
            tweet.id_str,
            tweet.created_at,
            tweet._json["created_at"],
            tweet.full_text,
            tweet_html_body(tweet, False),
            tweet_html_body(tweet, True),
            media,
            tweet.entities,
            qts,
            rt_of,
            tweet._json["in_reply_to_status_id_str"],
            tweet.user.screen_name,
            tweet.user.name,
            user_pfp,
            datetime.datetime.utcnow(),
        )

        return infltweet

    @property
    def profileimg_b64(self):
        return base64.b64encode(self.profileimg).decode()


class InflatedTweetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, InflatedTweet):
            return obj.__dict__
        if isinstance(obj, Replacement):
            return obj.__dict__
        if isinstance(obj, TweetMediaAttachment):
            return obj.__dict__
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode()
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class InflatedTweetDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        """Automatically detect the shape of custom objects we have"""
        infltweet_fields = [
            "id",
            "date",
            "date_original_format",
            "full_text",
            "media",
            "entities",
            "username",
            "user_displayname",
            "user_pfp",
        ]
        is_inflated_tweet = all([f in obj for f in infltweet_fields])
        if is_inflated_tweet:
            return InflatedTweet(**obj)

        mediaatt_fields = ["width", "height", "alttext", "url", "data"]
        is_media_att = all([f in obj for f in mediaatt_fields])
        if is_media_att:
            return TweetMediaAttachment(**obj)

        return obj


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
    with open(filename, "w") as fp:
        json.dump(infltweet, fp, cls=InflatedTweetEncoder, indent=2)


def tweet2data(
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

    filename = f"data/twarchive/{tweetid}.json"

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

    infltweet = InflatedTweet.from_tweet(tweet)
    with open(filename, "w") as fp:
        json.dump(infltweet, fp, cls=InflatedTweetEncoder, indent=2)
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
        try:
            tweet2data(
                api, tweetid=reltweet, force=force, rlevel=rlevel, max_rlevel=max_rlevel
            )
        except tweepy.errors.NotFound:
            # This appears to mean the tweet (or account) were intentionally deleted
            logger.warning(f"Could not find tweet with ID {reltweet}")
        except tweepy.errors.Forbidden as exc:
            # This appears to happen when the account was suspended
            exc_message = str(exc).replace("\n", " ")
            logger.warning(
                f"Not permitted to access tweet with ID {reltweet}: {exc_message}"
            )


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


def inline2data(
    consumer_key: str, consumer_secret: str, max_rlevel: int, force: bool = False
):
    """Save tweets to data that have been inlined

    Does not redownload items already saved.
    """
    api = authenticate(consumer_key, consumer_secret)
    for tweetid in find_inline_tweets():
        if tweetid.endswith("-intentionallyinvalid"):
            logger.info(f"Skipping intentionally invalid tweet id {tweetid}")
        else:
            tweet2data(api, tweetid=tweetid, force=force, max_rlevel=max_rlevel)


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


def usertweets2data(
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

    downloaded_tweets = get_downloaded_tweets()
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
        tweet2data(api, tweet=tweet, force=force, max_rlevel=max_rlevel)
