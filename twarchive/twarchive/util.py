"""Internal utilities"""

import os
import re


def uri_is_tweet(uri: str) -> bool:
    """Return whether a URI points to a single tweet"""
    return bool(re.match("https\:\/\/twitter\.com\/.*\/status\/[0-9]+", uri))


def tweeturi2tweetid(uri: str) -> str:
    """Given a tweet URI, return just the tweet ID it contains"""
    m = re.match("https\:\/\/twitter\.com\/.*\/status\/(?P<tweetid>[0-9]+)", uri)
    return m["tweetid"]


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
