# Optional style advice

These are prompts for the writer, not claims that the Finnish is wrong. No
actor is invented and no replacement text is generated. Everything runs in
the local Voikko pipeline. No model downloads, paid services or text uploads.
The normal grammar/spelling baseline is unchanged when this feature is off.

## LibreOffice

Tools > Add-Ons > Punakynä style advice... (Finnish UI: Työkalut > Lisäosat >
Punakynän tyylivinkit...). The extension adds this entry in Writer. All
preferences are off/unset initially:

- Prefer active: consider naming the actor when the reader needs to know who
  acts. The message explicitly says passive may be appropriate.
- Narrator: no preference / minä / me.
- Reader address: no preference / sinä / te.

Narrator and reader are separate: “Me lähetämme hakemuksen sinulle” is not a
person inconsistency. Third-person actors are not banned. `te` may mean plural
or polite singular. Settings apply to all Finnish documents, not a hidden
per-document inference. Turn them off for fiction, dialogue, quoted material
or other genres where a single narrator/address preference is inappropriate.
The dialog states this scope. Settings are saved atomically in
`~/.config/punakyna/style.json` (or `$PUNAKYNA_CONFIG/style.json`). A corrupt or
missing settings file falls back to off. New callbacks read changes; reopen
the document to have previously checked text checked again.

## CLI and API

```
python -m punakyna --prefer-active --narrator me --reader sina text.txt
```

`POST /check`: `{"text":"...", "style_profile":{"prefer_active":true,
"narrator":"me", "reader":"sina"}}`. Omit `style_profile` for no style
preferences. Values are validated; unknown fields or invalid values get 400.
The CLI flags affect its local checks and its `--serve` default profile.

Python: `check_text(text, style_profile={...})` or `StyleProfile` from
`punakyna.style`. Outputs use `category=style`, `severity=style`, no automatic
replacement, with `STYLE_ACTOR` / `STYLE_PERSON` identifiers. Grammar and
spelling diagnostics win on overlapping spans; style does not suppress them.

## Deliberate limits

- Morphology only, no semantic understanding of who is speaking. Hints ask the
  writer to check whether the expression refers to the selected role. They do
  not assert that a change of perspective is an error.
- At most one person-consistency hint per role per sentence.
- Ambiguous verb/noun and passive/imperative forms are skipped (e.g. `voimme`,
  `lähetä`). The first version covers unambiguous finite passives, not every
  compound passive, participle or colloquial form.
- Sentences/paragraphs containing quotation marks, code delimiters, quoted
  lines or URLs are conservatively skipped. This can miss unquoted prose in
  the same input; it avoids changing a quoted speaker's person. It is not a
  complete rich-text/code detector.
- Bare minä/me/sinä/te pronouns, unambiguous finite verbs and unambiguous
  possessive suffixes are covered. Not every inflected pronoun is covered.
- No style-quality accuracy claim: existing smoke evaluation is a regression
  check of the default grammar baseline, not a style benchmark.

## Language guidance

- Kotus: [Pidä ohjeet selkeinä - vältä passiivia](https://kotus.fi/pida-ohjeet-selkeina-valta-passiivia/).
  Clear instructions may need a visible actor; passive remains useful when
  the actor is unimportant, general or sensitive.
- Kielitoimiston ohjepankki: [Miten viitata tekstin vastaanottajaan?](https://kielitoimistonohjepankki.fi/vk/sopiva-savy-toimivat-ohjeet-ja-kysymykset/miten-viitata-tekstin-vastaanottajaan/).
  Address depends on genre/tone; pronouns, finite verbs and possessive suffixes
  express sinä/te. A narrator can legitimately say `we` while addressing `you`.

## Validation status

Unit/API/native-morphology checks and a real Linux LibreOffice 7.3 installed
component/menu/settings-dialog save plus subsequent proofreader callback were
checked. The dialog was visually inspected. This is not a macOS GUI pass;
that remains a separate delivery gate. No new macOS package or public release
is implied by this source PR.
