# Punakynä for LibreOffice

## Bundled macOS test package

The Apple-silicon OXT bundles the Python engine, arm64 native libraries,
Finnish dictionary and component license texts. Normal use needs no checkout,
Homebrew, pip, enrollment or manually started server. Intel Macs are not
covered by this build.

1. Stop the old manually started Punakynä server with Ctrl+C, or restart the
   Mac. This one-time cleanup prevents server fallback from hiding a bundled
   engine failure during testing.
2. Remove the old Punakynä extension in Tools > Extension Manager, then quit
   LibreOffice completely.
3. Add `punakyna-full-macos.oxt` in Extension Manager and restart LibreOffice.
4. Set the document language to Finnish. Test `Me olen likaisia.` with F7.
   The expected suggestion is `olen` to `olemme`. Check the right-click menu
   too, and verify that applying the suggestion changes the document.

Validation limits: the bundled engine loaded and checked text standalone in
macOS CI with no Homebrew library fallback. That is not a test inside
LibreOffice.app. Native loading, bundled Python compatibility, and applying a
correction in macOS LibreOffice still require the user's test. The earlier
manual-server path did show an F7 explanation and suggestion, a blue grammar
underline, and the context-menu suggestion on the user's Mac. Correction
application was not confirmed.

The extension prefers the local engine and can fall back to a configured
loopback server. `PUNAKYNA_LO_MODE=local` forces local mode;
`PUNAKYNA_LO_MODE=server` forces the legacy server path. Text stays local.
Background grammar underlines may still require an enabled Finnish spelling
provider in LibreOffice. Installing Voikko can replace the configured Finnish
proofreader list: re-enable Punakynä in Writing Aids if needed.

## Build and source distribution

`make_oxt.py` packs the engine and, when present, the `bundle/` staging tree.
`ci_collect_macos.py` and `bundle_native.py` collect the pinned sources,
licenses, native library closure and dictionary, then relink and check the
closure. See `SOURCES-README.md`. Distribute the corresponding-source archive
alongside the OXT. Do not treat short-lived Actions artifacts as permanent
source distribution.

The packaging workflow is manual-only. Do not run builds or upload artifacts
until account-wide storage cost clearance is established. Standard public
runner compute being free does not establish free artifact storage.

## Legacy developer server path

For development only: install libvoikko and its Finnish dictionary, run
`python -m punakyna --serve`, enroll with
`python -m punakyna --enroll-app libreoffice`, build with `make_oxt.py`, and
install the resulting OXT. The server preflight checks native engine setup at
startup. This is not the normal bundled-package installation flow.

## macOS crash/signature regression gate

The first bundled test build failed in LibreOffice 26.8.2.2 on macOS 15.8.1:
CODESIGNING / Invalid Page during ctypes dlopen. Relinking had invalidated
the embedded signatures. All final dylibs must now be ad-hoc signed AFTER
load-command edits, pass strict codesign verification, and pass the final
OXT's cross-platform CodeDirectory page-hash check. Do not bypass OS signing
checks or modify LibreOffice.app to work around a bad package.

On a real arm64 Mac, run `test_macos_host.py --oxt <finished.oxt>
--uno-python <Python-with-LibreOffice-uno>`. It uses a disposable profile,
refuses an existing server on 8377, forces local mode, inserts the regression
text, waits for background checking, calls the real proofreader through UNO,
applies a suggestion programmatically and checks document text/process
survival. The number in the test is a dummy. This harness is NOT a simulation
and refuses other platforms. It needs a real LibreOffice/UNO Python setup.

Before delivery, additionally verify in the actual Mac GUI: visible Finnish
grammar underline, F7 suggestion, and applying the suggestion through the UI.
The harness's programmatic replacement does not prove these UI interactions.
Record OXT SHA-256, macOS/LibreOffice versions, exact commands and outcomes.
Unrun tests are not passes. No Actions build or upload is authorized until
the separate account-wide storage-cost gate is cleared.
