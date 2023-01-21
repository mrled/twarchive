# twarchive

twarchive is a set of projects for archiving tweets for Hugo static sites.

* `twarchive` is also the name of a program for downloading tweet data to a local archive,
  written in Python.
  Tweets are stored in high fidelity locally,
  and remain accessible even if they are deleted on Twitter,
  the user gets suspended or deletes their account,
  etc.
  [See the `twarchive` readme](twarchive/readme.md).
* `ornithography` is a utility theme for Hugo that displays tweets downloaded by the Python script.
  I call it a _utility theme_ because it includes only the files necessary for displaying archived tweets.
  It doesn't have any styles, partials, or layouts for regular site pages,
  and can be used alongside any regular Hugo theme.
  It includes shortcodes `twarchiveTweet` and `twarchiveThread`.
  All tweets it displays are downloadable by users to a single HTML file.
  It uses no Twitter styles or Twitter JavaScript,
  but (unfortunately) JavaScript is required to get good UX for displaying them in an iframe.
  [See the `ornithography` readme](ornithography/readme.md).
* `aviary` is a second Hugo theme that can be used for creating a basic site.
  It's designed to be an option for users who want a dedicated site to keep a copy of all of their tweets,
  and don't already have a theme they want to use for that.
  It's used in the example site,
  and also at <https://tweets.micahrl.com>.
  [See the `aviary` readme](aviary/readme.md).
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

See [the howto](./docs/howto.md) for more details.

Some examples:

* [How the exampleSite was created](./docs/exampleSite.md);
  you can view the exampleSite by cloning the repo and running `make dev`.
* <https://tweets.micahrl.com> contains just my personal tweet archive and nothing else;
  you can see its source code [on GitHub](https://github.com/mrled/tweets.micahrl.com).

## Changelog

* Version 2 (`master` branch):
  * Separate aviary/ornithography themes
  * Support for tweet suggestions, disclaimers
* Version 1 (`v1` branch):
  * Initial release

