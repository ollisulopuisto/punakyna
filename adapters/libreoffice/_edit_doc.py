"""Testiapo: lisaa merkki kappaleen alkuun (siirtää korostusten positioita)."""
import sys
import time

import uno

para_idx = int(sys.argv[1])
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
assert ctx, 'UNO-silta ei noussut'
desktop = ctx.ServiceManager.createInstanceWithContext(
    'com.sun.star.frame.Desktop', ctx)
doc = desktop.getCurrentComponent()
enum = doc.Text.createEnumeration()
i = 0
while enum.hasMoreElements():
    p = enum.nextElement()
    if p.supportsService('com.sun.star.text.Paragraph'):
        if i == para_idx:
            p.Start.setString('X')
            print('edit ok')
            sys.exit(0)
        i += 1
sys.exit(1)
