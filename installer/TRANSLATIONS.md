The Simplified Chinese installer catalog is vendored from Inno Setup's official
translation by Zhenghan Yang (Kira), retaining its original attribution:
https://github.com/jrsoftware/issrc/blob/6ef32198ef1f7b7b375cd4b6b90896c2a58eb4c2/Files/Languages/ChineseSimplified.isl

It targets Inno Setup 6.5.0+ and is included locally because some Inno Setup 6
installations do not bundle Chinese. French, Japanese, Russian and German use
the compiler's bundled catalogs. Build output must contain no missing-message
warnings. ChineseOverrides.isl and JapaneseOverrides.isl specify UI fonts;
runtime font selection in Cropperio.iss provides ordered Windows fallbacks.
All local ISL/ISS files use UTF-8 with BOM for Inno Setup's Unicode detection.

Cropperio-specific shortcuts and launch labels are in Cropperio.iss. The GPL
license text is the unchanged original English legal text.
