"""Testiapo: luo Writer-asiakirja annetulla tekstillä (ajetaan /usr/bin/python3:lla)."""
import sys
import time

import uno

text = sys.argv[1]
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext(
    'com.sun.star.bridge.UnoUrlResolver', local)
ctx = None
for _ in range(60):
    try:
        ctx = resolver.resolve(
            'uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext')
        break
    except Exception:
        time.sleep(0.5)
assert ctx, 'LibreOffice UNO -silta ei noussut'
desktop = ctx.ServiceManager.createInstanceWithContext(
    'com.sun.star.frame.Desktop', ctx)
doc = desktop.loadComponentFromURL('private:factory/swriter', '_blank', 0, ())
cursor = doc.Text.createTextCursor()
paras = text.split('\n')
LINE_BREAK = uno.getConstantByName('com.sun.star.text.ControlCharacter.LINE_BREAK')
PARA_BREAK = uno.getConstantByName('com.sun.star.text.ControlCharacter.PARAGRAPH_BREAK')
for i, p in enumerate(paras):
    for j, piece in enumerate(p.split('\x0b')):
        doc.Text.insertString(cursor, piece, False)
        if j < len(p.split('\x0b')) - 1:
            doc.Text.insertControlCharacter(cursor, LINE_BREAK, False)
    if i < len(paras) - 1:
        doc.Text.insertControlCharacter(cursor, PARA_BREAK, False)
print('doc ok')
