# Desktop-pet localization contract

Complete the mandatory bilingual language question in `SKILL.md` before inspecting or generating assets. Do not infer a language or silently use the template's Simplified Chinese copy.

## Language record

Normalize the confirmed choice to a BCP 47 locale and pass both values to `new_project.py`:

- Simplified Chinese: language `简体中文`, locale `zh-CN`;
- English: language `English`, locale `en`;
- other: preserve the user's language name and choose the matching locale; ask only when a regional variant changes the result.

Keep one release language. A runtime language switch is optional and must not replace the confirmed build language. If the selected language is unsupported by the target installer technology, stop and explain the limitation instead of falling back silently.

## Required surfaces

Localize all of these into the confirmed language:

1. all 13 state names, bubble titles and bubble bodies;
2. click, drag, reminder and work-state messages;
3. right-click menu, settings panel, scale choices, notification and autostart controls;
4. system tray menu;
5. accessibility labels, button labels and image alternative text;
6. native permission, validation and user-facing error messages;
7. Windows/macOS installer UI when supported by that packaging target;
8. `DESKTOP_PET_USER_GUIDE.txt` and `DESKTOP_PET_STATE_TRIGGER_GUIDE.md`;
9. any generated image text, if text was explicitly requested. Prefer text-free character assets.

Developer-only identifiers, filenames, event IDs, process names and code comments may remain English. Do not translate stable asset IDs such as `new-message` or `break-reminder`.

## Review and release gate

After localization, set `localization_ready: true` in `project-spec.json` and write `output/reviews/localization-decision.json`:

```json
{
  "ok": true,
  "version": "1.0.0",
  "pet_language": "English",
  "pet_locale": "en",
  "surfaces": {
    "motion_bubbles": true,
    "state_labels": true,
    "context_menu": true,
    "settings_panel": true,
    "tray_menu": true,
    "accessibility_labels": true,
    "native_errors_and_permissions": true,
    "installer_ui": true,
    "user_guide": true,
    "state_trigger_guide": true
  },
  "reviewed_files": [
    "src/petMotions.ts",
    "src/petStates.ts",
    "src/IdlePreview.tsx",
    "src/App.tsx",
    "src-tauri/src/lib.rs",
    "src-tauri/tauri.windows.conf.json",
    "DESKTOP_PET_USER_GUIDE.txt",
    "DESKTOP_PET_STATE_TRIGGER_GUIDE.md"
  ]
}
```

Review the actual native app, not only source files. Confirm that no clipped text, mixed-language copy, untranslated fallback, encoding damage or wrong reading direction remains. Then run:

```powershell
python <skill>/scripts/validate_localization.py --project <project>
```

Changing the confirmed language invalidates the decision and requires a complete localization review again.
