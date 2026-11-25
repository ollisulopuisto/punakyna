# Kielitoimiston ohjepankki: rule candidates

Source: https://kielitoimistonohjepankki.fi/ (Kotus, CC BY-NC-ND 4.0 per the site footer).
This file holds only our own paraphrased rule notes and page links. No page text is copied
here; the crawled dataset is private working material and is not in this repository.

Crawl (2026-11-07, robots.txt allows): 729 Finnish pages: 630 ohje, 52 hno (names guide),
37 vk (virkakieli), 10 service pages. Topic areas on the home page: Merkit, numerot ja
lyhenteet; Nimet; Sana; Lause; Tyylivalinnat, otsikot, luetelma.

Status key: **done** = implemented with tests; **read** = page read, rule designed, not
implemented; **title** = only the title was reviewed, the page still has to be read before
any rule is written.

## Tier A: mechanical, high precision (implemented or next)

| Candidate | Page (path under /ohje/) | Status |
| --- | --- | --- |
| number + % needs a space (10 %) | prosenttimerkki | done v0.1.8 TYPO_PERCENT_SPACE |
| number + € $ £ needs a space | rahasummat | done v0.1.8 TYPO_CURRENCY_SPACE |
| clock time with a dot, no leading zero (style, not error) | ajanilmaukset-kellonajat-merkinta-ja-taivutus | done v0.1.8 TYPO_CLOCK_FORMAT |
| dot after esim., jne., tms., yms., huom. | lyhenteet-pisteelliset | done v0.1.8 TYPO_ABBR_DOT |
| date as d.m.yyyy with a dot after day and month, no space | ajanilmaukset-paivays-ja-vuosiluku | read |
| en dash in ranges (kello 9–12, 1995–2003) instead of hyphen | ajatusviiva-rajakohdat-ja-osapuolet-20-29-vuotiaat-suomi-ruotsi-maaottelu | read |
| decimal comma, not decimal point | luvut-ja-numerot-desimaaliluvut | read (ambiguous with dates and versions, so narrow context only) |
| 4+ digit numbers grouped by spaces from the end | luvut-ja-numerot-numeroiden-ryhmittely | done v0.1.17 TYPO_NUMBER_GROUP (5+ digits always, 4 only before a unit) |
| eaa. / eKr. forms | ajanilmaukset-eaa-vai-ekr | read: both types are acceptable in general text, no rule (2026-11-22) |
| ss./vv. are outdated, use s. and v. | lyhenteet-pisteelliset ("Tiesitkö?" box) | done v0.1.17 ABBR_SS_VV |

## Tier B: punctuation (commas are the most common real-world error class)

| Candidate | Page (path under /ohje/) | Status |
| --- | --- | --- |
| comma between main clause and mutta/vaan + full main clause | pilkku-ja-mutta-vaan | done v0.1.18 PUNCT_COMMA_MUTTA_VAAN |
| missing comma before a subordinate conjunction (että, jos, kun, ...) | pilkku-ja-alistuskonjunktiolla-esim-etta-jos-alkava-lause | done v0.1.19 PUNCT_COMMA_SUBORD |
| missing comma before a joka/mikä relative clause | pilkku-ja-joka-mika-relatiivilause | done v0.1.19 PUNCT_COMMA_RELATIVE |
| missing comma between two full main clauses (ja/tai/sillä) | pilkku-paalauseiden-valissa | done v0.1.20 PUNCT_COMMA_RINNASTUS |
| superfluous comma before kuin in comparisons | pilkku-kuin-ilmauksissa | done v0.1.20 PUNCT_COMMA_KUIN |
| missing comma after quote before attribution clause | pilkku-lainauksen-ja-johtolauseen-jaljessa | done v0.1.20 PUNCT_COMMA_JOHTOLAUSE |

Still **title** only; each needs the page read and a false-positive sweep before any rule:
pilkku-ja-infinitiivirakenteet, pilkku rinnasteisten lauseenjäsenten ja luettelon osien välissä,
epäsuoran kysymyslauseen pilkku, lainausmerkit ja vuorosanaviiva. Voikko's own grammar checker does not flag a missing comma
before että (verified 2026-11-25); its code 18 heuristic covers some joka cases with a
generic message, which PUNCT_COMMA_RELATIVE now supersedes with a precise one.

## Tier C: word-level (needs lexical knowledge, medium precision)

yhdyssana-vai-ei pages (about 20), yhdysmerkki pages, alkukirjain pages (months and seasons are
already covered by the lowercase-names rule), taivutustyyppeja pages, vierassanojen taivutuspaate,
ajan-ja-maaran-ilmauksia (luin tunnin / en lukenut tuntia). All **title**.

## Tier D: syntax and usage (low precision, advisory only)

verbi yksikossa tai monikossa (partly covered by SV_NUMBER_NONOLLA), predikatiivi pages,
rektioita pages, sanajarjestys, lauseenvastikkeet (style tier), passiivi (speech forms stay
unflagged), pronominit (hän vai se: speech forms stay unflagged), konjunktiot pages
(mutta vai vaan was read: both are standard in different registers, so not an error rule).

## Not rule material

Name guides (hno, nimet), country and place spelling choices (Nimenvalinta pages), the
food-industry word lists (Ruoka-alan ...), source citation and layout pages.
