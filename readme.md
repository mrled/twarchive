# twarchive

`twarchive` is a Hugo utility theme and Python script for archiving tweets.

Tweets are stored in high fidelity locally,
and remain accessible even if they are deleted on Twitter,
the user gets suspended or deletes their account,
etc.

Tweets archived this way use no Twitter styles or Twitter JavaScript
(but (unfortunately) JavaScript is required to get good UX for displaying them in an iframe).

## How it works

After installing the companion Python script:

```sh
pip install --user --upgrade twarchive
```

Run the `twarchive` command to download tweets you're interested in.
It saves not just the tweet,
but any attached media,
profile pictures,
retweeted or quote-tweeted tweets,
and previous tweets in the reply chain.

Tweets are saved to `data/twarchive/` as JSON.
Additionally, Markdown pages are created under `content/twarchive/`,
which creates the `twarchive` section in Hugo.
These Markdown pages are empty of content,
but have a `tweetid` in their front matter,
which the `twarchive` theme uses to generate two HTML pages for each tweet:
`index.html` for end-users to navigate to,
and `index.tweet.html` which contains the actual tweet page and is intended to be displayed in an iframe.

Python and the `tweepy` package are required only to run the `twarchive` script,
but are not needed for Hugo to build the site after tweet data is downloaded.
This project was designed so that you run the script manually and commit the results to your repo,
and production deployment (eg to Netlify) does not need Python.

## Using the Hugo theme with your site

You have to enable your site as a Hugo module.
Here's what I did for my site at <https://me.micahrl.com>.
(This theme is endorsed by YAML GANG, TOMLailures stay mad.)

```sh
cd /path/to/me.micahrl.com      # The git checkout dir for my site
hugo mod init me.micahrl.com    # Create a mod.go for my site
```

In your site's configuration file,
themes should be defined in a list,
using the go module name for the twarchive theme.
Here's my site's config.

```yaml

# Set up themes
theme:
- micahrl                       # My site's main theme, found at themes/micahrl
- cistercian                    # A secondary theme I made for my site, found at themes/cistercian
- github.com/mrled/twarchive    # twarchive theme, NOT checked out inside of themes/, used directly

# Set up media types
mediaTypes:
  text/html+tweet:
    suffixes: ["tweet.html"]

# Set up output formats
outputFormats:
  HtmlTweet:
    mediatype: text/html+tweet
    suffix: tweet.html
    isPlainText: true
    notAlternative: false
```

You'll to create the `twarchive` section in your site's content.
That means a file `content/twarchive/_index.md` with frontmatter like:

```md
---
title: Tweet archive
outputs:
    - HTML
cascade:
    outputs:
        - HTML
        - HtmlTweet
---

# Your tweet archive section page

Insert any content you want here
```

In your site's `<head>`, you'll want to import CSS and JavaScript.
Where this happens will depend on how your site is designed,
but my sites tend to have a Hugo partial containing the `<head>` element,
which might have lines like this:

```go-html-template
<head>
  <!-- ... -->
  {{- $twarchiveStyles := resources.Get "styles/twarchiveStyles.scss" | resources.ToCSS | resources.Fingerprint }}
  <link rel="stylesheet" href="{{ $twarchiveStyles.Permalink }}">

  <script>
    {{- partial "js/twarchiveTopFrame.js" | safeJS -}}
    twarchiveDisplayDataUri();
  </script>
</head>
```

You'll need to get the `twarchive` theme, with a command like:

```sh
hugo mod get
```

Now your site should be using the `twarchive` theme.
`hugo` should successfully build your site, etc.

## Customizing

The `twarchive` theme ships with some default layout files for
[`layouts/twarchive/section.html`](layouts/twarchive/section.html)
and [`layouts/twarchive/single.html`](layouts/twarchive/single.html).

You should feel free to copy those and override them by placing them in your site's
`layouts/twarchive/` directory (create it if it doesn't exist).

There is also a [`layouts/twarchive/single.tweet.html`](layouts/twarchive/single.tweet.html),
but you should not override this one.
This file creates the tweet iframes.
If you want these to be styled differently,
use CSS.

I have some recommendations:

```scss
// Light mode:
--twarchive-expanded-header-fg-color: var(--twarchive-twitter-lightgray);

// Dark mode:
--twarchive-expanded-header-fg-color: var(--twarchive-color-darkergray);
```

## Example site

I have a Hugo site at <https://tweets.micahrl.com> that contains just my tweet archive,
and nothing more.

You can see its source code, including a very barebones theme,
[on GitHub](https://github.com/mrled/tweets.micahrl.com).

## The `twarchive` command

```
> twarchive -h
usage: tweet [-h] [--debug] {tweet2json,tweet2data,showinlines,inline2data,data2md,examine,user2data} ...

Manage tweets

positional arguments:
  {tweet2json,tweet2data,showinlines,inline2data,data2md,examine,user2data}
    tweet2json          Download JSON for a tweet, including image data
    tweet2data          Download JSON for a tweet, and store it under
                        './data/twarchive/$tweetId.json', including any QTs or
                        parents
    showinlines         Show tweets inlined with the 'twarchiveTweet' shortcode
    inline2data         Download JSON for all tweets that are inlined via the
                        'twarchiveTweet' shortcode.
    data2md             Create a page under content/twarchive/ for every
                        downloaded tweet
    examine             Get the response from Twitter and launch the debugger
    user2data           Retrieve a user's full timeline from Twitter and store
                        in site data

optional arguments:
  -h, --help            show this help message and exit
  --debug, -d           Launch a debugger on unhandled exception
```

## Limitations

- `twarchive` uses v1.1 of the API, not v2. This means we do not support polls, but you can run the script out of the box without providing any credentials.

## Todo

- Rename `twarchiveRoot.scss`; it is only used internally and the name should reflect that.
- Support Twitter archive downloads too
  - Don't ever bother redownloading tweets that are already in a Twitter archive
  - But do download tweets referenced from a Twitter archive (RTs and thread parents)
