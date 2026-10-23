# Local author preview (LNG-034)

Build a preview from a package that passes the LNG-033 runtime validator:

```sh
python3 scripts/build_author_preview.py path/to/package.json
```

Open `.cache/author-preview/index.html` on the authoring machine. The builder
rejects invalid packages before writing a preview. It embeds package text in
the local HTML, so keep the output private. `.cache/` is ignored by Git and is
not included in the web build. There is no server upload, staff action, or
published draft route. Rebuilding replaces `index.html` and current asset
files; remove the local output directory when it is no longer needed.

To exercise real draft media, pass `--media-dir path/to/private/media`. Asset
`storageKey` values are resolved inside that directory, byte sizes checked,
and files copied to the local preview's `media/` directory. Without media,
the preview shows explicit unavailable states, image descriptions, and audio
transcripts. Audio controls use browser playback and the declared MIME type.

The preview steps through exercises in checkpoint order, shows prompt and
accessible name, displays hints and explanations, and compares responses
exactly with the authored primary response and variants. Wrong responses show
the expected answer and explanation; variants show their rationale. A 320px
frame and wide layout let authors inspect reflow. Browser tests cover these
states at desktop and mobile viewports.

This is a **provisional package check**. The current learner action records
`pending_evaluation` and has no authoritative scoring or feedback evaluator.
Construction and listening templates are shown as text entry until their
learner interactions are defined. Exact matching is intentionally strict; it
does not infer punctuation, case, diacritic, transliteration, or word-order
equivalence. LNG-050/LNG-056 must define and implement shared evaluator policy
before anyone can claim scoring parity. A full authoring workspace will be
considered after pilot authors demonstrate repeated use and specific editing
needs; no workspace or draft publication path is shipped here.
