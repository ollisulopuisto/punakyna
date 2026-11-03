"""libvoikko-sidonta. Kirjasto ladataan annetusta polusta tai jarjestelmasta."""
import os

import libvoikko

_VOIKKO = None


def get_voikko(lang='fi', lib_path=None, dict_path=None):
    global _VOIKKO
    if _VOIKKO is None:
        lib_path = lib_path or os.environ.get('PUNAKYNA_LIBVOIKKO_PATH')
        dict_path = dict_path or os.environ.get('PUNAKYNA_VOIKKO_DICTIONARY_PATH')
        if lib_path:
            libvoikko.Voikko.setLibrarySearchPath(lib_path)
        kwargs = {}
        if dict_path:
            kwargs['path'] = dict_path
        _VOIKKO = libvoikko.Voikko(lang, **kwargs)
        # Oikolukijan kayttotapaus: kappaleet voivat olla keskeneraisia
        # (muuten jokaiseen syotteeseen tulee haamuvika "loppuvalimerkki puuttuu").
        _VOIKKO.setAcceptUnfinishedParagraphsInGc(True)
    return _VOIKKO
