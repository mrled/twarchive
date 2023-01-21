# Customizing

The `ornithography` theme ships with some default layout files for
[`layouts/twarchive/section.html`](ornithography/layouts/twarchive/section.html)
and [`layouts/twarchive/single.html`](ornithography/layouts/twarchive/single.html).

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
