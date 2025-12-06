# How to

In short:

* Download some tweets using the `twarchive` Python script
* Enable the `ornithography` theme as a module in your Hugo site to display those tweets
* Either use the basic `aviary` theme,
  or add some JavaScript and CSS to your site's `<head>` element directly

See also [how exampleSite was created](./exampleSite.md).

## Download some tweets

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

You can also provide suggestions and disclaimers on tweets, if you like;
see [annotations](./annotations.md) for more info on this.

## Enable the `ornithography` theme

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
  tweet:
    basename: index.tweet
    # Process with Go's text/template, not html/template
    isPlainText: true
    mediaType: text/html
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
            - tweet
    ---

    # Your tweet archive section page

    Insert any content you want here
```

## Import `ornithography`'s CSS and JavaScript

To use `ornithography`, you'll need to import the CSS and JavaScript that makes tweet display work.
You have two options for this:

1. Import the resources in whatever theme you're already using
1. Use the `aviary` theme as your main site theme, which has the required stuff already built in

## Import `ornithography`'s resources into an existing theme

If you aren't using `aviary`,
you'll need to import CSS and JavaScript from `ornithography`
in your site's `<head>`.

Where exactly this happens will depend on how your site is designed,
but my sites tend to have a Hugo partial containing the `<head>` element,
which might have lines like this:

```go-html-template
<head>
  <!-- ... -->
  {{- $twarchiveStyles := resources.Get "styles/twarchiveStyles.scss" | css.Sass | resources.Fingerprint }}
  <link rel="stylesheet" href="{{ $twarchiveStyles.Permalink }}">

  <script>
    {{- partial "js/twarchiveTopFrame.js" | safeJS -}}
    twarchiveDisplayDataUri();
  </script>
</head>
```

### Enable the `aviary` theme

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
