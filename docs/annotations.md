# Tweet annotations: suggestions and disclaimers

`ornithography` has support for suggestions,
similar to the suggestion reasons that Twitter places above some tweets on its Home/For You page,
and disclaimers, similar to the fact checking that Twitter places below some misleading tweets.

To use these, you must

* Use the `twarchive` Python program to download tweet data to `data/twarchive/<tweetid>.json` and create a content file in `content/twarchive/<tweetid>.md`.
* Copy `content/twarchive/<tweetid>.md` to `content/twarchive/example.md`
* Add a `suggestion:` or `disclaimer:` field to the frontmatter in the newly created `example.md`

When `twarchive` creates the content file, it creates an empty markdown file with some YAML frontmatter.
For instance, here's the content file for the [most iconic tweet](https://twitter.com/jack/status/20):

```text
---
tweetid: "20"
date: 2006-03-21 20:50:14+00:00
---
```

That's the whole file.
The actual tweet data is stored in the JSON data file,
but the content file is necessary to get Hugo to render it.

So, in the copy you create at `content/twarchive/example.md`,
just add a field for a suggestion, a disclaimer, or both, like this:

```text
---
tweetid: "20"
date: 2006-03-21 20:50:14+00:00
suggestion: 🤠 We think you might want to see this
disclaimer: ℹ️ User-generated content may be misleading
---
```

Now you can reference the original with
`{{< twarchiveTweet "20" >}}`
(because `20` is the tweet ID)
and the annotated copy with
`{{< twarchiveTweet "example" >}}`.
