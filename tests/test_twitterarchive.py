"""Test twitterarchive.py"""

import os
import pathlib
import tempfile

from twarchive import twitterarchive


SCRIPTDIR = pathlib.Path(__file__).parent
TESTDATADIR = SCRIPTDIR.joinpath("data")
# TESTDATADIR = os.path.join(SCRIPTDIR, "data")
# TESTARCHIVE = twitterarchive.TwitterArchive.frompath(os.path.resolve(os.path.join(TESTDATADIR, "..")))
TESTARCHIVE = twitterarchive.TwitterArchive.frompath(TESTDATADIR.parent)

# class TestData:
#     path = TESTDATADIR
#     profilejs = os.path.join(TESTDATADIR, "mrled.profile.js")
#     tweetjs = os.path.join(TESTDATADIR, "mrled.tweet.js")


# TESTARCHIVE = twitterarchive.TwitterArchive(
#     TestData.path, TestData.profilejs, TestData.tweetjs, None, None, None
# )


def test_parse_twitter_window_YTD_bullshit():
    parsed = twitterarchive.parse_twitter_window_YTD_bullshit(TESTARCHIVE.profilejs)
    assert len(parsed) == 1
    assert parsed[0]["profile"]["description"]["location"] == "Austin"
    assert (
        parsed[0]["profile"]["headerMediaUrl"]
        == "https://pbs.twimg.com/profile_banners/35010911/1593300924"
    )

    parsed = twitterarchive.parse_twitter_window_YTD_bullshit(TESTARCHIVE.tweetjs)
    assert len(parsed) == 2


def test_archive2infltweets():
    with tempfile.TemporaryDirectory() as hugodata:
        twitterarchive.archive2data(TESTARCHIVE, api=None, hugodata=hugodata)
        tweetfiles = os.listdir(hugodata)
        # Don't forget: RTs are not saved when api=None
        assert len(tweetfiles) == 1
