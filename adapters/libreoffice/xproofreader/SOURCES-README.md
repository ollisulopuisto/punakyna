# Vastaava lähdekoodi: punakyna-full-macos.oxt

Tämä arkisto sisältää Punakynä LibreOffice -laajennuksen
(punakyna-full-macos.oxt) mukana tulevien käännettyjen komponenttien
**tarkan vastaavan lähdekoodin** sekä rakennusohjeen.

## Sisältö

- `*.tar.gz` / `*.tar.bz2` / `*.tgz`: alkuperäiset, muuttamattomat
  lähdepaketit. Versiot, lähdeosoitteet ja sha256-tarkistussummat on
  lueteltu laajennuspaketin tiedostossa `licenses/SOURCES.txt`.
  Summat varmennettiin rakennuksen yhteydessä.
- `build-recipe/`: täsmällinen rakennusohje (skriptit ja
  CI-työnkulkumäärittely), joilla jakeluun toimitetut binäärit
  tuotettiin.

## Miten binäärit tuotettiin

Binäärit on käännetty Homebrew:n kaavoista (macos-latest CI-ajaja,
arm64). Lähdekoodeihin EI tehty muutoksia. Ainoa binääreihin kohdistettu
muokkaus on dylib-tiedostojen install name -uudelleenkirjoitus
`@loader_path`-suhteisiksi (install_name_tool), jotta kirjastot löytävät
toisensa laajennuspaketin sisältä. Tämän tekee
`build-recipe/bundle_native.py` (funktio `_macos_fixups`), ja koko
ketjun (brew-asennus, riippuvuussulkeuma otool:lla, lataukset,
tarkistussummat, paketointi) ajaa `build-recipe/ci_collect_macos.py`
työnkulussa `build-recipe/build-full-oxt.yml`.

## Uusientaminen

macOS-koneella (arm64), jossa Xcode CLT ja Homebrew:

    brew install libvoikko
    git clone https://github.com/ollisulopuisto/punakyna
    cd punakyna
    python3 adapters/libreoffice/xproofreader/ci_collect_macos.py
    python3 adapters/libreoffice/xproofreader/make_oxt.py \
        dist/punakyna-full-macos.oxt

## Arkiston kokoaminen paloista (jos toimitettu osina)

    cat punakyna-corresponding-sources.tar.gz.part-* \
        > punakyna-corresponding-sources.tar.gz
    tar -tzf punakyna-corresponding-sources.tar.gz | head
