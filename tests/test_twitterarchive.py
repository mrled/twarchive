"""Test twitterarchive.py"""

import os
import tempfile

from twarchive import twitterarchive


MRLED_PROFILE_JS = """\
window.YTD.profile.part0 = [ {
  "profile" : {
    "description" : {
      "bio" : "It's a SYLLABIC R, dammit! Don't you speak English?",
      "website" : "https://t.co/qFJtWc3kHU",
      "location" : "Austin. Texas."
    },
    "avatarMediaUrl" : "https://pbs.twimg.com/profile_images/421501892/Micah_As_Ship_-_4.seal.white.png",
    "headerMediaUrl" : "https://pbs.twimg.com/profile_banners/35010911/1363586917"
  }
} ]
"""


def test_parse_twitter_window_YTD_bullshit():
    with tempfile.TemporaryDirectory() as tempdir:
        profilepath = os.path.join(tempdir, "profile.js")
        with open(profilepath, "w") as pfp:
            pfp.write(MRLED_PROFILE_JS)
        parsed = twitterarchive.parse_twitter_window_YTD_bullshit(profilepath)
    assert len(parsed) == 1
    assert parsed[0]["profile"]["description"]["location"] == "Austin. Texas."
    assert (
        parsed[0]["profile"]["headerMediaUrl"]
        == "https://pbs.twimg.com/profile_banners/35010911/1363586917"
    )
