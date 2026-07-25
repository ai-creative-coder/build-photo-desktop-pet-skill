# Build Photo Desktop Pet Skill

English | [简体中文](README.md)

Turn one photo of a person or animal into an installable desktop pet. Designed for Codex, this Skill covers chibi character production, 13 animated states, transparent-asset validation, Tauri integration, native runtime acceptance, and Windows/macOS release packaging.

## Features

- Derives the subject only from the current user's uploaded photo and never reuses another user's photo or character assets.
- Produces a proportion-validated chibi base and a six-view reference board.
- Generates and reviews a separate 12-frame transparent animation for each of 13 states.
- Detects ghosting, bobbing, irregular scaling, cropping, deformation, fragments, and unwanted shadows.
- Supports click greetings, drag encouragement, work activity, message alerts, and break reminders.
- Keeps the context menu away from the character and supports a 50%–100% pet scale range.
- Builds a lightweight desktop application with React, Vite, and Tauri.
- Supports Windows x64 NSIS delivery; macOS releases must be built on macOS.
- Uses Codex built-in ImageGen by default and provides an adapter for an explicitly approved external image provider.

## Included States

`idle`, `click`, `drag`, `stretch`, `thinking`, `coding`, `processing`, `debugging`, `error`, `drink-water`, `task-complete`, `new-message`, and `break-reminder`

## Installation

### Option 1: Download a release

1. Download the latest ZIP from the repository's **Releases** page.
2. Extract it and copy the `build-photo-desktop-pet` folder to:

   - Windows: `%USERPROFILE%\.codex\skills\`
   - macOS/Linux: `~/.codex/skills/`

3. Restart Codex or open a new task.

### Option 2: Clone the repository

```powershell
git clone https://github.com/chx-123/build-photo-desktop-pet-skill.git
Copy-Item -Recurse -Force `
  .\build-photo-desktop-pet-skill\build-photo-desktop-pet `
  "$env:USERPROFILE\.codex\skills\build-photo-desktop-pet"
```

## Usage

Upload a photo of a person or animal in Codex, then ask:

```text
$build-photo-desktop-pet Turn this photo into a desktop pet and produce a Windows installer.
```

By default, the Skill will:

1. Check the image, ImageGen, Python, Node.js, Rust, and target-native build tools.
2. Generate and review the base character, turnaround reference, and program icon.
3. Produce all 13 state animations independently.
4. Test interaction, transparency, menu placement, and scaling in the native Tauri window.
5. Build an installer only after the final quality gates pass.

## Requirements

- Codex with built-in ImageGen available.
- Python 3 and Pillow.
- Node.js and npm.
- A Rust toolchain.
- For Windows installers: Windows x64 and the required native build tools.
- For macOS releases: macOS and Xcode Command Line Tools; shareable releases also require Developer ID signing and notarization credentials.

Run a preflight check:

```powershell
python .\build-photo-desktop-pet\scripts\check_environment.py --json --target windows
```

## External Image Providers

If Codex built-in ImageGen is unavailable, the Skill stops before generation and asks for an external provider configuration. The current photo may be sent to that service only after the user explicitly approves it.

```powershell
python .\build-photo-desktop-pet\scripts\external_image_provider.py --check
```

See:

`build-photo-desktop-pet/references/image-provider-configuration.md`

## Privacy and Quality Guarantees

- Does not read typed text, clipboard contents, chats, document contents, or screen pixels.
- Uses the source photo only for the current project; it is excluded from the Skill package, reusable template, and final installer.
- Never uses another user's character, image, private path, or appearance prompt as an example or fallback.
- Re-runs release review for the exact encoded 13-state asset set and native runtime on every build.
- Blocks packaging when ghosting, shaking, irregular scaling, cropping, discontinuity, deformation, fragments, or character/floor shadows remain.

## Repository Layout

```text
.
├── README.md
├── README_EN.md
└── build-photo-desktop-pet/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

The README files live at the repository root and are not part of the Codex Skill runtime context. Only the `build-photo-desktop-pet` directory needs to be installed.

## Validation

```powershell
python .\build-photo-desktop-pet\scripts\audit_skill_privacy.py `
  .\build-photo-desktop-pet

python .\build-photo-desktop-pet\scripts\test_skill_guards.py

$env:PYTHONUTF8 = "1"
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" `
  .\build-photo-desktop-pet
```

## Platform Notes

- Windows builds produce a current-user NSIS installer.
- macOS builds must be produced and verified on a Mac.
- iPhone and iPad cannot use the desktop installer. Animation assets can be reused, but a separate signed iOS/iPadOS app is required.
- Unsigned Windows or macOS builds may trigger operating-system security warnings.
