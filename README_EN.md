# Build Photo Desktop Pet Skill

English | [简体中文](README.md)

Turn one photo of a person  into an installable chibi desktop pet. The character keeps the photo's most recognizable visual traits and accompanies the user through work, study, and breaks with expressive actions.

## Features

- Designs a personalized chibi character from the user's uploaded photo while preserving recognizable hair, clothing, accessories, markings, and other defining traits.
- Includes 13 states such as idle, click greetings, drag encouragement, thinking, coding, debugging, task completion, hydration, and break reminders, with actions and expressions that react naturally to user activity.
- Supports click interaction and free dragging; the context menu stays above and to the right without covering the pet, and the pet can be resized from 50% to 100%.
- Lets users turn message reminders on or off at any time and remembers their preference.
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

The Skill will:

1. Create a chibi base character and application icon from the photo.
2. Produce all 13 desktop-pet animation states.
3. Integrate click, drag, resize, message, and work-context interactions.
4. Produce an installable desktop-pet package for the current platform.

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

## Privacy

- Does not read typed text, clipboard contents, chats, document contents, or screen pixels.
- Uses the source photo only for the current project; it is excluded from the Skill package, reusable template, and final installer.
- Never uses another user's character, image, private path, or appearance prompt as an example or fallback.

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

## Platform Notes

- Windows builds produce a current-user NSIS installer.
- macOS builds must be produced and verified on a Mac.
- iPhone and iPad cannot use the desktop installer. Animation assets can be reused, but a separate signed iOS/iPadOS app is required.
- Unsigned Windows or macOS builds may trigger operating-system security warnings.
