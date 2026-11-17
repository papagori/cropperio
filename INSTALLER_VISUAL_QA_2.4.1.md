# Cropperio v2.4.1 — Manual installer visual QA

Status: **manual visual QA accepted by the user on 2026-11-17**.

The user reports manually inspecting the installer and application, with no
visible layout, translation or glyph issues. The user explicitly considers the
previous Computer Use limitation non-blocking and authorizes final validation
and stable publication.

This records user-provided visual acceptance, not a new assistant visual test.
Per-page screenshots, display scaling, Windows version and a language-by-language
checklist were not supplied with that acceptance and are not inferred here.
Automated coverage and install/run/uninstall results are recorded separately in
[TEST_REPORT.md](TEST_REPORT.md).

## Historical Computer Use investigation (2026-11-16)

Computer Use previously detected the installer window as a process-backed app
whose executable was `Cropperio_Setup.tmp` in an Inno Setup temporary directory.
Access was rejected with:

> Computer Use was not approved to use cropperio_setup.tmp

The [official Computer Use documentation](https://learn.chatgpt.com/docs/computer-use#permissions-and-approvals)
states that native app approvals are separate from file/shell permissions and
use the app identifier reported by Computer Use, including executable names on
Windows. For executable-name approvals, the temporary child should therefore be
treated as a separate approval target from `Cropperio_Setup.exe`; approving the
launcher alone does not establish approval for that child.

On the latest investigation, `cropperio_setup.tmp` was already present in the
current configuration's `computer_use.windows.always_allowed_app_ids`. A legacy
Computer Use configuration still listed only Python and Maya. These observations
do not establish which policy the running runtime applied or prove a migration
or caching defect.

The official `sky.launch_app` flow was attempted for the final installer. It
returned `launched app did not expose a targetable window`. Read-only process
inspection showed the launcher and its temporary child running, with the child's
parent PID matching the launcher. Subsequent official window enumeration exposed
no installer window, so a new child-window approval attempt could not be reached.
Native visual access remains unavailable; its underlying cause is unconfirmed.

The supported approval route is **ChatGPT Settings > Computer use**, enable
**Any App** if necessary, and approve the exact app in the official permission
prompt. No separate app-approval request API is exposed in this session's Computer
Use tool surface. The assistant did not alter permissions, use another capture
mechanism, or modify the installer to evade this restriction.

Automated installation, Unicode-path, translation and glyph checks have passed;
they do not certify the native installer page layout. This was the original release gate. The user subsequently completed manual
visual QA and explicitly accepted the Computer Use limitation as non-blocking.
