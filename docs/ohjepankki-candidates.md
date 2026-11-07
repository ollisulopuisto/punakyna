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
| 4+ digit numbers grouped by spaces from the end | luvut-ja-numerot-numeroiden-ryhmittely | read |
| eaa. / eKr. forms | ajanilmaukset-eaa-vai-ekr | title |
| ss./vv. are outdated, use s. and v. | lyhenteet-pisteelliset ("Tiesitkö?" box) | read |

## Tier B: punctuation (commas are the most common real-world error class)

All **title** only; each needs the page read and a false-positive sweep before any rule.
Highest value first: pilkku-ja-alistuskonjunktiolla-esim-etta-jos-alkava-lause (read: the
subordinate clause is separated by a comma; a "missing comma before että/jos/kun" rule needs
exceptions for short clauses, "Hyvin lyhyet lauseet: pilkku valinnainen", and combinations
such as "etenkin jos"), pilkku-ja-joka-mika-relatiivilause, pilkku-ja-mutta-vaan,
pilkku-paalauseiden-valissa, pilkku-kuin-ilmauksissa, pilkku-lainauksen-ja-johtolauseen-jaljessa.
Voikko's own grammar checker already covers some comma errors; overlap must be checked first.

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
