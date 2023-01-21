# The `twarchive` command

```text
> twarchive --help
usage: twarchive [-h] [--debug] {version,ls,internals,tweet2json,tweet2data,showinlines,inline2data,data2md,user2data,archive2data,show-inline-tweets} ...

Manage tweets

positional arguments:
  {version,ls,internals,tweet2json,tweet2data,showinlines,inline2data,data2md,user2data,archive2data,show-inline-tweets}
    version             Show program version
    ls                  List tweet files in a Hugo repository, sorted by tweet ID and accounting for tweet IDs of different lengths
    internals           Internal commands used in development
    tweet2json          Download JSON for a tweet, including image data
    tweet2data          Download JSON for a tweet, and store it under './data/twarchive/$tweetId.json', including any QTs or parents
    showinlines         Show tweets inlined with the 'twarchiveTweet' shortcode
    inline2data         Download JSON for all tweets that are inlined via the 'twarchiveTweet' shortcode.
    data2md             Create a page under content/twarchive/ for every downloaded tweet
    user2data           Retrieve a user's full timeline from Twitter and store in site data
    archive2data        Parse a Twitter archive extracted to twitter-archives/<name> and save the result to the Hugo data dir
    show-inline-tweets  Show a list of all tweets included by twarchive Hugo partials

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           Launch a debugger on unhandled exception
```

## Limitations

- `twarchive` uses v1.1 of the API, not v2. This means we do not support polls, but you can run the script out of the box without providing any credentials.
