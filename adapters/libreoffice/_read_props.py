"""Testiapo: lue kappaleen N alueen [start,end) CharUnderline-arvot (UNO)."""
import sys
import time

import uno

para_idx, start, end = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
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
target = None
while enum.hasMoreElements():
    p = enum.nextElement()
    if p.supportsService('com.sun.star.text.Paragraph'):
        if i == para_idx:
            target = p
            break
        i += 1
assert target is not None, f'kappaletta {para_idx} ei loydy'
cursor = doc.Text.createTextCursorByRange(target.Start)
cursor.goRight(start, False)
cursor.goRight(end - start, True)
print(f'underline={cursor.CharUnderline} color={cursor.CharUnderlineColor} '
      f'hascolor={cursor.CharUnderlineHasColor} text={cursor.getString()!r}')
