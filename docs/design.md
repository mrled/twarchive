# Design

These are a few notes on how the themes work.

## Terminology

* A **tweet ID** is a Twitter concept. Each tweet has an ID.
  `twarchive` downloads tweets by ID,
  and saves JSON tweet data under `data/twarchive/<tweetid>.json`.
* A **tweet instance** is a local reference to a tweet, usually under `content/twarchive/<tweetid>.md`.
  This is a Markdown file containing only frontmatter
  (actual tweet data is stored as a JSON data file, per above).
  These files may contain `suggestion:` or `disclaimer:` fields,
  which will render a tweet with annotations.
  (Typically you should copy `content/twarchive/<tweetid>.md` to `content/twarchive/<newname>.md`),
  so that your archive contains an un-annotated copy of any tweet you wish to annotate.)
  See [annotations](./annotations.md) for more information.
