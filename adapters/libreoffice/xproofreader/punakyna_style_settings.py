# -*- coding: utf-8 -*-
"""Optional style advice settings. Explicit profile, no document rewrites."""
import os
import uno
import unohelper
from com.sun.star.task import XJob
from com.sun.star.lang import XServiceInfo

import sys
if '__file__' in globals():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NAME = 'org.punakyna.comp.StyleSettings'


from punakyna.style_settings import load_profile, save_profile


class StyleSettings(unohelper.Base, XJob, XServiceInfo):
    def __init__(self, ctx):
        self.ctx = ctx

    def getImplementationName(self):
        return NAME

    def getSupportedServiceNames(self):
        return (NAME,)

    def supportsService(self, service):
        return service == NAME

    def execute(self, args):
        from punakyna.style import StyleProfile
        sm = self.ctx.ServiceManager
        profile = load_profile()
        model = sm.createInstanceWithContext('com.sun.star.awt.UnoControlDialogModel', self.ctx)
        model.Width = 265
        model.Height = 190
        model.Title = 'Punakynä: tyylivinkit'
        def add(kind, name, x, y, w, h, **props):
            item = model.createInstance('com.sun.star.awt.UnoControl' + kind + 'Model')
            item.PositionX, item.PositionY, item.Width, item.Height = x, y, w, h
            for key, value in props.items():
                setattr(item, key, value)
            model.insertByName(name, item)
            return item
        add('FixedText', 'scope', 8, 6, 248, 25,
            Label='Valinnaisia vinkkejä, ei virheitä. Koskee kaikkia suomenkielisiä asiakirjoja. Ei muuta tekstiä.', MultiLine=True)
        active = add('CheckBox', 'active', 8, 35, 248, 14,
                     Label='Ehdota tekijän ilmaisemista (suosi aktiivia)', State=int(profile.prefer_active))
        add('FixedText', 'narrator_label', 8, 56, 245, 12, Label='Kertoja: minä- ja me-muodon johdonmukaisuus')
        narrator = add('ListBox', 'narrator', 8, 70, 245, 14,
                       StringItemList=('Ei valintaa', 'minä', 'me'), Dropdown=True,
                       SelectedItems=(('any', 'mina', 'me').index(profile.narrator),))
        add('FixedText', 'reader_label', 8, 91, 245, 12, Label='Lukijan puhuttelu: sinä- ja te-muodon johdonmukaisuus')
        reader = add('ListBox', 'reader', 8, 105, 245, 14,
                     StringItemList=('Ei valintaa', 'sinä', 'te (monikko tai teitittely)'), Dropdown=True,
                     SelectedItems=(('any', 'sina', 'te').index(profile.reader),))
        add('FixedText', 'limits', 8, 126, 248, 22,
            Label='Monitulkintaiset muodot ja lainaukset ohitetaan. Näkökulman vaihto voi olla tarkoituksellinen.', MultiLine=True)
        add('FixedText', 'refresh', 8, 151, 248, 19,
            Label='Asetus tulee voimaan seuraavissa tarkistuksissa. Tarkista aiempi teksti avaamalla asiakirja uudelleen.', MultiLine=True)
        add('Button', 'cancel', 133, 171, 58, 15, Label='Peruuta', PushButtonType=2)
        add('Button', 'save', 197, 171, 58, 15, Label='Tallenna', PushButtonType=1, DefaultButton=True)
        dialog = sm.createInstanceWithContext('com.sun.star.awt.UnoControlDialog', self.ctx)
        dialog.setModel(model)
        toolkit = sm.createInstanceWithContext('com.sun.star.awt.Toolkit', self.ctx)
        dialog.createPeer(toolkit, None)
        try:
            if dialog.execute() == 1:
                selected = StyleProfile(bool(active.State),
                    ('any', 'mina', 'me')[narrator.SelectedItems[0]],
                    ('any', 'sina', 'te')[reader.SelectedItems[0]])
                save_profile(selected)
        finally:
            dialog.dispose()
        return None


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(StyleSettings, NAME, (NAME,))
