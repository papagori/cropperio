# Cropperio v2.4.1 — Release notes

Stable Windows release. The user completed manual visual inspection of the
installer and application and reported no visible layout, translation or glyph
issues. The earlier Computer Use limitation is non-blocking; see
[the visual QA record](INSTALLER_VISUAL_QA_2.4.1.md).

- Added a discreet link to discover more software and updates from the developer.
  **More Software & Updates** appears in the existing footer beside GitHub and
  opens https://www.matthieutuffet.com/software/ in the default browser on request.
- Added complete Simplified Chinese (简体中文), Russian (Русский) and German
  (Deutsch) interfaces and Windows installer translations. Cropperio now supports
  six languages, including English, French and Japanese.
- Language preferences persist across restarts and apply to startup text.
- Localized the presentation text and added Chinese font preferences and layout
  safeguards for longer translations.

No advertising dialogs, automatic update checks, background network requests,
telemetry, new dependencies or license changes.

## Link labels

| Language | Label |
| --- | --- |
| English | More Software & Updates |
| Français | Autres logiciels et mises à jour |
| 日本語 | その他のソフトウェアと更新情報 |
| 简体中文 | 更多软件与更新 |
| Русский | Другие программы и обновления |
| Deutsch | Weitere Software und Updates |

## Interface and localization notes

There is no existing Help menu or About dialog. The existing footer already holds
the license and GitHub link, so the new link uses the same keyboard-accessible
label, styling and Qt default-browser integration there, without duplication.
Browser-launch failures return safely without opening an error dialog.

All application-owned strings are translated. Native Windows file-picker controls
follow the Windows display language; Qt's fallback dialogs load the selected Qt
translation. External OS/codec exception details and the original GPL legal text
are retained verbatim. Automated coverage checks establish completeness and matching placeholders;
they do not constitute a native-speaker editorial certification.

See [TEST_REPORT.md](TEST_REPORT.md) for validation and
[installer/TRANSLATIONS.md](installer/TRANSLATIONS.md) for installer catalog provenance.
