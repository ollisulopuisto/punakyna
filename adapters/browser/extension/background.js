// Punakynä-tausta: välittää tekstin native-isännälle. Tekstiä ei lähetetä
// verkkoon - ainoa ulosmenevä kanava on selaimen hallitsema native messaging.
const HOST = 'fi.punakyna.host';

chrome.action.onClicked.addListener(async (tab) => {
  const [{result}] = await chrome.scripting.executeScript({
    target: {tabId: tab.id},
    func: () => (window.getSelection() || '').toString(),
  });
  if (!result || !result.trim()) return;
  try {
    const resp = await chrome.runtime.sendNativeMessage(HOST, {text: result});
    await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: (r) => { /* TODO: inline-korostukset; nyt konsoliin */
        console.log('Punakynä-löydökset:', r); },
      args: [resp],
    });
  } catch (e) {
    console.error('Punakynä-isäntä ei vastaa (rekisteröitykö manifesti?):', e);
  }
});
