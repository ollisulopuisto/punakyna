# Finnish grammar rule inventory (plan, v0.1.1)

Status: PLAN. No implementation beyond the rules listed as "have". Written
2026-11-07 after the "Minä olen menty" miss (PR #19). Aim: replace one-off
rules with a systematic, sourced inventory. Each rule gets: id, source,
positive tests, false-positive guards, and a row in the coverage map below.

## Rule record (required for every rule)

| field | content |
|---|---|
| id | `CATEGORY_NAME`, stable |
| source | VISK § number (+URL) first; Kielitoimiston ohjepankki / sanakirja or Kotus for norm questions; no source = no rule |
| scope | what it checks, what it deliberately skips |
| tests | >= 3 positive, >= 3 guards (valid sentences that look similar) |
| severity | `error` only when the norm is unambiguous (VISK/ohjepankki "norminmukainen"); `style`/`info` for variation, speech-like forms, contested usage |
| data | rule table in a data file (verb lists, lemma sets), not inline code |

Registry file (to build): `punakyna/rules_data/*.yaml|py` + one test module
per category + `eval/` smoke lines. A script generates the coverage map from
the registry so docs cannot drift.

## Sources, in priority order

1. VISK, Iso suomen kielioppi, https://scripta.kotus.fi/visk/ (Kotus). Parts:
   Sanat / Rakenne / Ilmiöt. Descriptive, includes spoken variation: use for
   "what is grammatical", and for guards.
2. Kielitoimiston ohjepankki, https://www.kielitoimistonohjepankki.fi/
   (Kotus). Normative standard-language advice: use for what to mark as error.
   Topics: Merkit/numerot/lyhenteet, Nimet, Sana, Lause, Tyylivalinnat.
3. Kielitoimiston sanakirja, https://www.kielitoimistonsanakirja.fi/ : word
   forms, inflection types, spelling.
4. Hyvän virkakielen ohjeet (ohjepankin välilehti): style tier only.

Not sources: forum pages, language-learning sites, model knowledge.

## What exists today

Voikko GC (libvoikko 4.3.3 `src/grammar/error.hpp`, codes 1-18): invalid
spelling; extra whitespace / space before punctuation; extra comma;
sentence starter; first-letter case (lower/upper); repeating word; missing
terminating punctuation; quotation/parenthesis punctuation; negative verb
mismatch (13); A-infinitive required (14); MA-infinitive required (15);
misplaced sidesana (16); missing main verb (17); extra main verb (18).
Punakynä layers (have): DOUBLE_WORD, NEG_CONNEGATIVE, NEG_NUMBER,
SV_AGREEMENT (olla only), PRON_VERB_AGREEMENT, CAP_COMMON_NOUN,
PERFECT_PASSIVE_PARTICIPLE (PR #19), optional Stanza parser tier, style
advice profiles.

## Categories, sources, coverage, priority

Coverage: have = rule exists; GC = Voikko GC covers; none = gap. Priority
1 = high frequency in native writing AND checkable with morphology only
(precision first); 2 = needs sentence structure; 3 = parser/neural or
contested norm.

| # | Category | Primary source (VISK chapter / ohjepankki) | Coverage | Prio |
|---|---|---|---|---|
| 1 | Compound-tense participle form (olen menty; §1292, §530, §1534) | VISK Passiivi; Tempus | have (limited verb list) | 1: extend |
| 2 | Subject-verb / pronoun-verb agreement (kongruenssi) | VISK Kongruenssi | have (narrow) | 1: extend to all finite verbs, not only olla |
| 3 | Negation: neg. verb + connegative, ei + 1/2 pers. | VISK Kielto ja kielteiset ilmaukset | GC 13 + have | 1: verify gaps (imperative älä, "ei" + finite) |
| 4 | Predicative/attribute agreement in number and case (isot talo, hyvä ruoat) | VISK Kongruenssi; Adjektiivit | none | 1 |
| 5 | Infinitive / participle government (A-, MA-, E-inf.; "pyrkii tehdä") | VISK Infinitiivit ja partisiitit; Verbit | GC 14, 15 partial | 2 |
| 6 | Case government: verbs/adpositions (pre/postpositio + genetiivi/partitiivi) | VISK Adpositiot; Sijamuotojen syntaksia | none | 2 |
| 7 | Object case (akkusatiivi/partitiivi/nominatiivi) | VISK Sijamuotojen syntaksia | none | 3 (needs parse) |
| 8 | Numeral + noun case/number (kaksi talo, 5 kirjaa) | VISK Numeraalit; ohjepankki Lause: yksikkö ja monikko | none | 1 |
| 9 | Passive: personal passive "me mennään" is speech; "ollaan menty" | VISK §1292 | partial (guards) | 2 |
| 10 | Comparison (isompi kuin vs isompaa; superlative forms) | VISK Komparaatio | none | 2 |
| 11 | Compound words, hyphenation (yhdyssanavirhe, sanaliitto, väli-viiva) | VISK Yhdyssanat; ohjepankki Sana | spelling GC partial | 1 (needs resource, see ROADMAP 3) |
| 12 | Capitalisation (months, days, institutions, nationality words) | ohjepankki Sana: alkukirjain | have (months) + GC 6/7 | 1: extend |
| 13 | Punctuation: commas before että/joka/jotta/koska; quotation marks; dashes | ohjepankki Merkit; VISK Yhdyslauseet | GC 3/4/10-12 partial | 2 |
| 14 | Numbers, units, abbreviations (spacing, 3. vs 3, kello 10.00) | ohjepankki Merkit, numerot, lyhenteet | none | 1 |
| 15 | Possessive suffix and reflexive (hän ... omaa; sen takia ... -nsa) | VISK Pronominit; Possessiivisuffiksi | none | 3 |
| 16 | Word order / missing or extra main verb | VISK Sanajärjestys | GC 16-18 (style) | 3 |
| 17 | Anglicisms/calques; "tehdä sense", "olla tarvetta" | ohjepankki Tyylivalinnat; Sana: vierassanat | none | style-only |
| 18 | Passive overuse, active voice, person consistency | docs/style-advice.md | have (opt-in) | n/a |

## Method (per category)

1. Read the VISK section(s) and the ohjepankki entry; record URL, quote the
   norm in the rule header (short), and the norm vs variation line.
2. List the surface patterns the morphology layer can detect (Voikko
   analyses: CLASS, SIJAMUOTO, NUMBER, PERSON, PARTICIPLE, FSTOUTPUT).
3. List guards from the VISK exceptions (e.g. §1292 double passive, "ei oltu
   tehty"; §530 transitive passive participles as predicatives).
4. Implement as table + generic checker, test, run `eval/evaluate.py` on the
   clean set; any new flag on clean text blocks the rule (AGENTS.md).
5. Measure on held-out data when available (ROADMAP 1: FinnGEC/DaLA; DaLA is
   synthetic). Report per-category precision, not only recall.

## Proposed order

1. Registry + coverage-map generator + migrate the 5 existing rule
   families onto it (no behaviour change; tests prove equivalence).
2. Cat. 1 and 2 generalised (all finite verbs, all participle forms).
3. Cat. 4 and 8 (number/case agreement; numeral+noun).
4. Cat. 12, 14 (capitalisation, numbers/units/abbreviations) from the
   ohjepankki.
5. Cat. 11 once a compound resource is cleared (ROADMAP 3).
6. Cats. 5, 6, 9, 10 with parser tier; cat. 7, 15, 16 research only.

## Open questions for Olli

- Severity policy: is "norm" = Kielitoimisto standard language always, or
  is speech-like (me ollaan) accepted as no-flag? Current default: no flag.
- Priority between precision (few flags) and recall for the first release.
- Is a licensing check of VISK text reuse needed? Plan: cite and paraphrase,
  never copy VISK passages or example sentences into the repo.
