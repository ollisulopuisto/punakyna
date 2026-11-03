// Punakynä NSSpellServer-delegaatti - LUONNOS, EI KÄÄNNETTY EIKÄ TESTATTU.
// Vahvistamatta: checkGrammar-delegaatin toimivuus nyky-macOS:lla.
import Foundation

final class PunakynaSpellDelegate: NSObject {
    // TODO(Mac): kutsu paikallista rajapintaa http://127.0.0.1:8377/check
    // bearer-tunnuksella (~/.config/punakyna/token). Positiot: NSSpellServer
    // käyttää UTF-16-NSRangeja - sama muunnos kuin LO-sovittimen offsets.py.

    @objc func spellServer(_ sender: NSSpellServer,
                           findMisspelledWordIn stringToCheck: String,
                           language: String,
                           wordCount: UnsafeMutablePointer<Int>,
                           countOnly: Bool) -> NSRange {
        // TODO(Mac): toteuta. Älä koskaan tulkita tiedostopolkuja pyynnöistä
        // (DirtyDict CVE 2025 -luokka, ks. docs/macos-integration.md).
        return NSRange(location: NSNotFound, length: 0)
    }

    @objc func spellServer(_ sender: NSSpellServer,
                           suggestGuessesForWord word: String,
                           inLanguage language: String) -> [String]? {
        return nil  // TODO(Mac)
    }

    // AVOIN: onko tämä tuettu nyky-macOS:lla? Historiallisesti kaatanut
    // VoikkoSpellServicen. Vahvista ennen käyttöönottoa.
    @objc func spellServer(_ sender: NSSpellServer,
                           checkGrammarIn stringToCheck: String,
                           language: String,
                           details: AutoreleasingUnsafeMutablePointer<NSArray?>?) -> NSRange {
        return NSRange(location: NSNotFound, length: 0)  // TODO(Mac)
    }
}

@main
struct PunakynaServiceMain {
    static func main() {
        let server = NSSpellServer()
        if server.registerLanguage("Finnish", byVendor: "Punakynä") {
            server.delegate = PunakynaSpellDelegate()
            server.run()
        }
    }
}
