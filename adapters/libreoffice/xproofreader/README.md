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
