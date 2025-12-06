# Creating the exampleSite from scratch

This is how the `./exampleSite` was created.
It uses both `aviary` and `ornithography`,
and doesn't require any other theme.
It's a useful example of how to make a standalone tweet archive site.

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
    - tweet

outputFormats:
  tweet:
    basename: index.tweet
    # Process with Go's text/template, not html/template
    isPlainText: true
    mediaType: text/html
    notAlternative: false

params:
  dateform: "2006-01-02 03:04:05 -07:00"

disableKinds:
  - taxonomy
```

Get the aviary and ornithography themes as modules,
and start the site in dev mode.

```sh
hugo mod get -u
hugo serve --port 40404 &
```
