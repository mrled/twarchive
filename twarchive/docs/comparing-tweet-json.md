# Comparing tweet json

You can use the command `twarchive internals json-load-dump-tweets` to load all tweets stored in data/twarchive/*.json,
and save them out with the latest version of the JSON encoder.

When making a big change to how tweets are stored, you might want to diff the result and sanity check it.

- Get a fresh copy of the git repo
- Copy `data/twarchive` to something like `data/old-twarchive`
- Run `twarchive internals json-load-dump-tweets` to make your changes.
  The new format is now in `data/twarchive`.
- Cd to `data/old-twarchive`
- Run `for f in *; do diff <(jq --sort-keys . < "$f") <(jq --sort-keys . < "../twarchive/$f"); done`

Adapted from the very helpful <https://github.com/jlevy/pdiffjson>.
