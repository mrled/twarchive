# twarchive

twarchive is a set of projects for archiving tweets for Hugo static sites.

* `twarchive` is also the name of a program for downloading tweet data to a local archive,
  written in Python.
  Tweets are stored in high fidelity locally,
  and remain accessible even if they are deleted on Twitter,
  the user gets suspended or deletes their account,
  etc.
* `ornithography` is a utility theme for Hugo that displays tweets downloaded by the Python script.
  I call it a _utility theme_ because it includes only the files necessary for displaying archived tweets.
  It doesn't have any styles, partials, or layouts for regular site pages,
  and can be used alongside any regular Hugo theme.
  It includes shortcodes `twarchiveTweet` and `twarchiveThread`.
  All tweets it displays are downloadable by users to a single HTML file.
  It uses no Twitter styles or Twitter JavaScript,
  but (unfortunately) JavaScript is required to get good UX for displaying them in an iframe.
* `aviary` is a second Hugo theme that can be used for creating a basic site.
  It's designed to be an option for users who want a dedicated site to keep a copy of all of their tweets,
  and don't already have a theme they want to use for that.
  It's used in the example site,
  and also at <https://tweets.micahrl.com>.
* The `exampleSite` showcases all of these:
  it uses `aviary` as its base site theme,
  includes `ornithography` for displaying the archived tweets,
  and relies on tweet data downloaded via the `twarchive` Python program.

## How it works

In short:

* Download some tweets using the `twarchive` Python script
* Enable the `ornithography` theme as a module in your Hugo site to display those tweets
* Either use the basic `aviary` theme,
  or add some JavaScript and CSS to your site's `<head>` element directly

### Download some tweets

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

### Enable the `ornithography` theme

You have to enable your site as a Hugo module.
Here's what I did for my site at <https://me.micahrl.com>.

```sh
cd /path/to/me.micahrl.com      # The git checkout dir for my site
hugo mod init me.micahrl.com    # Create a mod.go for my site
```

In your site's configuration file,
themes should be defined in a list,
using the go module name for each theme.
Here's my main website's config as an example.
(This theme is endorsed by YAML GANG, TOMLailures stay mad.)

```yaml

# Set up themes
theme:
- micahrl                                     # My site's main theme, found at themes/micahrl
- cistercian                                  # A secondary theme I made for my site, found at themes/cistercian
- github.com/mrled/twarchive/ornithography    # The ornithography theme, NOT checked out inside of themes/, used directly

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


### Import `ornithography`'s CSS and JavaScript

To use `ornithography`, you'll need to import the CSS and JavaScript that makes tweet display work.
You have two options for this:

1. Import the resources in whatever theme you're already using
1. Use the `aviary` theme as your main site theme, which has the required stuff already built in

### Import `ornithography`'s resources into an existing theme

If you aren't using `aviary`,
you'll need to import CSS and JavaScript from `ornithography`
in your site's `<head>`.

Where exactly this happens will depend on how your site is designed,
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
#### Enable the `aviary` theme

Instead,
you can use the basic `aviary` theme
if you're building a new site to hold your tweet archive
and you don't already have a theme you want to use for it.
(If you do already have a theme, don't use `aviary`, and skip to the next section instead.)

Add it to the `theme` key in your site's configuration.
See the `exampleSite`, which uses:

```yaml
module:
  imports:
  - path: github.com/mrled/twarchive/aviary           # The aviary theme, which should come first
  - path: github.com/mrled/twarchive/ornithography    # The ornithography theme, which should come at the end
```

Then you'll have to tell Hugo to download the modules:

```sh
hugo mod get -u
```

## Example: Creating the exampleSite from scratch

This is how the `./exampleSite` was created.

Create the site skeleton:

```sh
mkdir exampleSite
cd exampleSite
hugo new site .
rm config.toml
hugo mod init twarchive.example.org
```

Save a `config.yml` file:

```yaml
baseURL: http://twarchive.example.org
languageCode: en-us
title: twarchive example site

module:
  imports:
    - path: github.com/mrled/twarchive/aviary
    - path: github.com/mrled/twarchive/ornithography

mediaTypes:
  text/html+tweet:
    suffixes: ["tweet.html"]

outputs:
  home:
    - HTML
  section:
    - HTML
    - HtmlTweet

outputFormats:
  HtmlTweet:
    mediatype: text/html+tweet
    suffix: tweet.html
    isPlainText: true
    notAlternative: false

params:
  dateform: "2006-01-02 03:04:05 -07:00"

disableKinds:
  - taxonomy
  - taxonomyTerm
```

Get the aviary and ornithography themes as modules,
and start the site in dev mode.

```sh
hugo mod get -u
hugo serve --port 40404 &
```

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

## Todo

- Rename `twarchiveRoot.scss`; it is only used internally and the name should reflect that.
- Support Twitter archive downloads too
  - Don't ever bother redownloading tweets that are already in a Twitter archive
  - But do download tweets referenced from a Twitter archive (RTs and thread parents)
- Why do I have both `thread_parent_id` and `replyto_tweetid` ??
