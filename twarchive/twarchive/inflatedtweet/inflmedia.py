"""Retrieving media from tweets

TODO: would be nice to DRY these functions out
"""

import os
import typing

import requests

from twarchive import util
from twarchive.inflatedtweet.inflatedtweet import TweetMediaAttachment

if typing.TYPE_CHECKING:
    from twarchive.twitterarchive import TwitterArchive


def get_media_photo(
    item: typing.Dict, tweetid: str, archive: typing.Optional["TwitterArchive"]
) -> TweetMediaAttachment:
    # if item["type"] == "photo":
    w = item["sizes"]["small"]["w"]
    h = item["sizes"]["small"]["h"]
    alttext = item.get("media_alt_text", "")
    url = item["media_url_https"]
    mime = item.get("content_type", util.guess_mime_type(url))
    if archive:
        url_filename = url.split("/")[-1]
        media_filename = f"{tweetid}-{url_filename}"
        media_path = os.path.join(archive.tweetmedia, media_filename)
        with open(media_path, "b") as mfp:
            data = mfp.read()
    else:
        data = requests.get(url).content
    attachment = TweetMediaAttachment("photo", mime, w, h, alttext, url, data)
    return attachment


def get_media_video(
    item: typing.Dict, tweetid: str, archive: typing.Optional["TwitterArchive"]
) -> TweetMediaAttachment:
    # if item["type"] == "video":
    w = item["sizes"]["small"]["w"]
    h = item["sizes"]["small"]["h"]
    alttext = item.get("media_alt_text", "")
    variants = {
        int(v["bitrate"]): v for v in item["video_info"]["variants"] if "bitrate" in v
    }
    best_bitrate = max(variants.keys())
    variant = variants[best_bitrate]
    url = variant["url"]
    mime = variant.get("content_type", util.guess_mime_type(url))
    if archive:
        url_filename = url.split("/")[-1]
        media_filename = f"{tweetid}-{url_filename}"
        media_path = os.path.join(archive.tweetmedia, media_filename)
        with open(media_path, "b") as mfp:
            data = mfp.read()
    else:
        data = requests.get(url).content
    attachment = TweetMediaAttachment("video", mime, w, h, alttext, url, data)
    return attachment


def get_media_gif(
    item: typing.Dict, tweetid: str, archive: typing.Optional["TwitterArchive"]
) -> TweetMediaAttachment:
    # if item["type"] == "animated_gif":
    w = item["sizes"]["small"]["w"]
    h = item["sizes"]["small"]["h"]
    alttext = item.get("media_alt_text", "")
    variants = {
        int(v["bitrate"]): v for v in item["video_info"]["variants"] if "bitrate" in v
    }
    best_bitrate = max(variants.keys())
    variant = variants[best_bitrate]
    url = variant["url"]
    mime = variant.get("content_type", util.guess_mime_type(url))
    if archive:
        url_filename = url.split("/")[-1]
        media_filename = f"{tweetid}-{url_filename}"
        media_path = os.path.join(archive.tweetmedia, media_filename)
        with open(media_path, "b") as mfp:
            data = mfp.read()
    else:
        data = requests.get(url).content
    attachment = TweetMediaAttachment("animated_gif", mime, w, h, alttext, url, data)
    return attachment


def get_all_media(
    extended_entities: typing.Dict,
    tweetid: str,
    archive: typing.Optional["TwitterArchive"],
) -> typing.List[TweetMediaAttachment]:
    media: typing.List[TweetMediaAttachment] = []
    for item in extended_entities.get("media", []):
        if item["type"] == "photo":
            attachment = get_media_photo(item, tweetid, archive)
            media += [attachment]
        elif item["type"] == "video":
            attachment = get_media_video(item, tweetid, archive)
            media += [attachment]
        elif item["type"] == "animated_gif":
            attachment = get_media_gif(item, tweetid, archive)
            media += [attachment]
        else:
            raise Exception(
                f"Unknown item type {item['type']} trying to download media for tweet {tweetid}"
            )
    return media
