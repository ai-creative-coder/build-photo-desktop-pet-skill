---
name: build-photo-desktop-pet
description: Turn one uploaded photo of a person or animal into a consistent animation-ready chibi subject, multi-view reference, 13 transparent desktop-pet states, stable 12-frame animations, and a lightweight Tauri desktop pet with Windows x64 NSIS and optional macOS app/DMG delivery. Use when a user asks to make a Q-version/cartoon desktop companion, desktop pet, alpha sprite animations, or a distributable Windows or Mac desktop installer from a human or animal image, including end-to-end generation, repair, validation, packaging, or reuse of this workflow. Route iPhone/iPad requests through the separate platform-compatibility rules.
---

# Build a photo-based Windows or macOS desktop pet

Convert one person or animal image into a production desktop pet. Continue autonomously with safe defaults; ask only when the intended subject is ambiguous, the image omits critical identity structure, a tool/fallback requires explicit permission, or a quality gate cannot be passed without a user choice.

Never use a previous user's photo, generated character, animation, prompt containing private appearance details, source path or project-specific visual asset as a bundled example, fallback, placeholder or style reference. Generate every subject asset only from the current user's uploaded image. The bundled template uses one explicitly authorized generic standing chibi only as a pre-generation application icon; it is not an identity, clothing, proportion or style reference. Never ship that bundled placeholder in a finished user's installer.

## Required companion skill and references

Before any visual generation or edit, read and follow the installed `imagegen` skill completely. Inside Codex, use the built-in `image_gen` tool by default. If it is unavailable or the Skill runs outside Codex, stop before generation, tell the user that an external image model/API must be configured, read `references/image-provider-configuration.md`, and use the provider-neutral adapter only after the user approves sending the current photo to that provider. Never silently switch providers or fallbacks.

Read these bundled references when entering the matching phase:

- Character, ImageGen, alpha and animation work: `references/visual-production.md`
- State behavior, priorities, privacy and interaction: `references/state-runtime-contract.md`
- Validation, packaging and handoff: `references/quality-and-delivery.md`
- Non-Codex/external image provider setup: `references/image-provider-configuration.md`
- iPhone/iPad, macOS and Windows output boundaries: `references/platform-compatibility.md`

Do not load all references before they are needed.

## Defaults

Unless the user specifies otherwise, use:

- Target: Windows x64, current-user NSIS installer.
- Product name: `我的桌宠`.
- Style: polished warm chibi illustration preserving visible identity, morphology, markings, accessories and palette.
- States: the 13-state contract in `references/state-runtime-contract.md`.
- Motion: 12 frames, `384x341 RGBA`; 140 ms interaction frames and 180–220 ms slow frames.
- Transparency: built-in ImageGen on a removable flat chroma key, then local alpha removal and validation.
- Image provider: Codex built-in ImageGen when available; otherwise an explicitly configured external provider through `scripts/external_image_provider.py`.
- Program icon: the current user's approved neutral standing RGBA chibi base, uniformly fitted as a full-body icon.
- App: bundled React/Vite/Tauri template.
- Privacy: local metadata only; never read key values, document/chat content, clipboard or screen pixels.
- Operation mode: proceed end-to-end after self-review. Show milestone previews when useful, but require approval only if the user explicitly requests checkpoints or a gate has multiple materially different valid outcomes.

When the user requests macOS or both desktop platforms, build the Mac release separately on macOS. Do not promise universal compatibility. State each tested OS, architecture, signing and notarization status.

## Output workspace

Create a new project-specific directory. Never write generated assets only under the image tool's default output path.

```text
<project>/
├─ input/                         # copied source image
├─ character/
│  ├─ character-spec.md
│  ├─ base/
│  └─ turnaround/
├─ states/<state>/
│  ├─ source/
│  ├─ keyposes/
│  ├─ masks/
│  ├─ frames_alpha/
│  └─ review/
├─ public/assets/pet/integrated-v1/
├─ output/reviews/
└─ output/releases/
   ├─ windows/
   └─ macos/
```

Copy the current user's source image non-destructively. Do not include it in the installer, skill package, template or reusable examples. Do not reuse any other user's source or derived asset.

## Phase 0 — preflight

1. Locate the uploaded image and inspect it with the image-viewing tool.
2. Determine the target platform. Default to Windows x64 when unspecified. For macOS, both desktop platforms, iPhone or iPad, read `references/platform-compatibility.md`. If “Apple desktop” is ambiguous, ask whether the user means iOS/iPadOS or macOS.
3. Run for the selected desktop target:

   ```powershell
   python <skill>/scripts/check_environment.py --json --target <windows|macos>
   ```

4. Confirm the generation provider. In Codex, require the built-in ImageGen tool. Outside Codex or when that tool is unavailable, explain that the user must configure an image model and API, then validate the external adapter with `external_image_provider.py --check`; do not send the photo until the user explicitly approves that provider.
5. If Pillow alone is missing, install `scripts/requirements.txt` into the active Python environment when authorized by the task. If Node, Rust or target-native build tools are missing, continue visual/project work when useful but report that installer creation for that platform is blocked.
6. If multiple people or animals could be the subject, ask one concise question. Otherwise choose the dominant intended subject and proceed.
7. Create `character-spec.md` from visible facts. For a person, record hair, face, wardrobe and shoes. For an animal, record body shape, coat/feather/scale pattern, ears, muzzle/beak, paws/hooves/wings, tail and visible collar/harness. Do not guess a breed or sensitive attribute when uncertain.
8. Record the original pose, occluded regions, identity accessories, explicit removal list and minimal-inference list. Default every character/state asset to no floor plane, cast/contact shadow or reflection in addition to the neutral-base removals.

Success: source is inspectable, subject is unambiguous, output workspace and toolchain status are recorded.

## Phase 1 — chibi identity and turnaround

1. Use the source as the sole identity/appearance reference and generate one full-body chibi base on a flat key color.
2. For an upright person or anthropomorphic subject, default to `2.6–2.7` heads with the head approximately `37–39%` of total height, head width slightly greater than shoulder width, compact limbs and a fixed sole baseline. For natural animals, preserve species geometry and select a recorded readable chibi ratio instead of forcing human proportions.
3. Measure the selected base from highest hair/hat point to chin and from highest point to the shared sole baseline. Run `validate_character_proportions.py`, save its JSON/overlay, and reject the base unless the measured ratio is `2.6–2.7` heads and the head fraction is `37–39%`. A prompt that merely requests the ratio is not evidence.
4. Remove every listed handheld/carried object, unwanted bag/strap, scene prop, text and effect. Keep approved worn identity accessories. Require complete relaxed empty hands or species-appropriate extremities and a self-supporting neutral pose.
5. Inspect face, silhouette, morphology, markings, accessories, anatomy, cropping and fine edges. For animals, preserve species-appropriate paws, wings, hooves or fins unless the user explicitly requests anthropomorphic hands. Iterate one targeted change at a time.
6. Save both the flat chroma-key master and geometry-identical RGBA master. Use magenta instead of green when the subject contains substantial green.
7. Generate a multi-view board: front, side, back, front three-quarter, back three-quarter and detail views.
8. Compare every view to `character-spec.md`. Freeze the approved identity, measured ratio, body scale and contact-baseline invariants.
9. Save prompts, measured landmark coordinates, proportion report and selected image paths in `character/generation-log.md`.

Reject identity drift, changed clothing/markings, missing fingers/paws, residual object-gripping poses, cropped hair/ears/tail/shoes, whole-subject rescaling during head revisions and spatially impossible anatomy or accessories.

Success: one reusable base and a consistent turnaround exist; the approved neutral standing RGBA base is frozen as the program-icon source.

## Phase 2 — plan and generate 13 state stills

1. Copy the state contract into `state-plan.md` and tailor only user-requested text/style changes.
2. Generate each state in a separate call through the approved provider from the approved base. Do not generate all states as independent cells of one sheet.
3. Keep the same subject, appearance, style, approved ratio and global scale. Adapt actions to human hands, paws, wings or other anatomy without silently redesigning the subject. Add furniture, keyboard, monitor, cup or other props only when functionally required by that state; the neutral-base cleanup rule does not prohibit state-specific props. Check physical logic.
4. Convert chroma-key sources with the installed imagegen `remove_chroma_key.py` helper.
5. Inspect checkerboard, white and dark composites. Clean hair, fingers, shoes, enclosed chair/table gaps and translucent RGB fringe. Reject any generated floor, cast/contact shadow or reflection, including under furniture.

Success: all 13 state stills are RGBA, visually consistent and named by state.

## Phase 3 — prove the animation method

Build `thinking` and `coding` before batching other states.

- Thinking proves face, blink, expression and detached icon masks.
- Coding proves a locked over-the-shoulder/rear three-quarter scene, clean alternating typing hands and visible changes on the monitor front. The character faces the monitor; the viewer may see the character's back and the screen front at an oblique angle. Never place the changing screen content on the monitor back.

Use a single static base only for genuinely local motion. Use 2–5 same-lineage full-body/full-scene key poses when motion crosses anatomy. Every proof loop must visibly change at least two semantic elements from expression, joint pose, gaze, held prop or prop state. Never cross-dissolve two complete redrawn characters or scenes: it creates double-image ghosting. Hold clean key poses on the 12-frame timeline and encode every hold explicitly with full-frame source blending. Never play an ImageGen 4x3 storyboard directly. Never align by full alpha bounds or scale frames independently. Never mesh-warp fingers or keyboards.

Before approving either proof, declare one subject-scale landmark that is not changed by the action or detached props, such as head width, hat width, shoulder width, or head-top-to-contact distance. Measure it again from the three normalized, decoded key poses. Reject the proof when a height landmark spans more than 1 px or a width landmark spans more than 2 px. If the action occludes or changes one landmark, select a different stable landmark; do not silently fall back to full alpha bounds.

Produce 12 precomposited alpha frames and run:

```powershell
python <skill>/scripts/make_animation.py `
  --frames-dir <state>/frames_alpha `
  --out-dir <state>/review `
  --asset-name <asset-name> `
  --frame-ms <duration>
```

Inspect storyboard, onion skin, full-size playback and enlarged face/moving-extremity details. If either proof state shakes, scales, cuts anatomy, warps hands/paws/wings or shows fragments, fix the production method before creating the remaining animations.

Success: both proof states pass mechanical and visual review.

## Phase 4 — animate all states

For each state:

1. Write a 12-frame action rhythm.
2. Write `motion-plan.json` declaring the user/OS trigger, changing expressions, changing joints, changing props/effects, fixed anchors and the 12-frame key-pose schedule.
3. Choose local layers only for changes contained inside a stable outline.
4. Use full key poses for chin/hair/wrist/sleeve/shoulder/waist/held-prop changes.
5. Keep one source canvas and one global uniform transform.
6. Align stable lower anchors; require `baseline_y_range = 0` for non-locomotion desktop-pet loops and separately inspect pelvis, shoulders and head.
7. Save the chosen subject-scale landmark and its decoded three-key-pose measurements in the state validation report. Require a range of at most 1 px for height landmarks or 2 px for width landmarks.
8. Extract effects with exact masks; person/effect overlap must be zero unless deliberately attached.
9. Export with `make_animation.py` and keep `validation.json`.

For `drag`, require an unmistakable encouragement arc: determined effort/cheer pose while dragging, then a positive smile, wink, fist/thumbs-up or celebratory effect. Start it at the 7 px movement threshold, keep it active throughout the drag and let it settle after release without restarting frame 1.

Do not use whole-subject vertical/horizontal oscillation, sinusoidal scale, per-frame fit, camera movement, irregular wobble or full-subject cross-dissolves as the primary animation. Legitimate repeated hold frames may preserve timing, but the APNG writer must keep all 12 explicit full frames with `blend=source`; do not add one-pixel glints/noise merely to defeat duplicate-frame collapsing. Every unique pose must come from a legitimate expression, joint, prop, effect or transition change. Do not freeze the lower body when the upper-body pose changes the center of mass. Do not use rectangular crops that include hair or fingers. Remove unexplained black blocks, shoe fragments and adjacent-storyboard contamination.

Success: 13 stable 12-frame animation sets pass their review artifacts.

## Phase 5 — scaffold and integrate the app

Create the project from the bundled generic template:

```powershell
python <skill>/scripts/new_project.py `
  --out <project> `
  --product-name "<name>" `
  --slug <ascii-slug> `
  --version 1.0.0
```

Replace the bundled generic chibi placeholder with icons derived from the current user's approved neutral standing RGBA base:

```powershell
python <skill>/scripts/generate_project_icons.py `
  --source <project>/character/base/<approved-standing-alpha.png> `
  --project <project>
```

Use the full neutral standing subject, not a state pose with a chair, monitor, cup, effect, text or speech bubble. Inspect `output/reviews/program-icon-review.png` at 256, 128, 64 and 32 px. Require readable identity, complete silhouette, unchanged proportions and no clipping. The script writes project-specific PNG, ICO and ICNS files and records only the source SHA256—not the private source path—in `project-spec.json`.

Copy final animated assets to `public/assets/pet/integrated-v1` using exactly the filenames in the runtime contract. Keep source/keypose/review assets outside `public`.

Package only one active 13-state asset set. If an older set must remain under `public` for review, copy the active runtime files to release-qualified, globally unique basenames and point the runtime contract at those names. A versioned directory alone is not sufficient because native resource packaging can resolve an older same-named file.

Run:

```powershell
python <skill>/scripts/validate_pet_assets.py `
  <project>/public/assets/pet/integrated-v1
```

Do not build while this validator reports errors or while `custom_icon_ready` is false.

Review the template's process/tool allowlists against the user's current environment. Verify time-sensitive process names locally instead of assuming old executable names remain correct. For macOS, implement or verify the macOS activity, permission and login-item adapter before claiming parity with Windows.

Success: all 13 assets load, the user's standing-base program icon passes small-size review, and the browser preview can cycle states without console errors.

## Phase 6 — runtime acceptance

Verify in the Tauri app, not only the browser:

- transparent, borderless, always-on-top bottom-right launch with no console window;
- click under 7 px triggers greeting; real movement at least 7 px moves the window and triggers cheer;
- right-click random preview, size, notification access, autostart and exit;
- bubble fixed at top-right and scaled with the pet at 50%, 85% and 100%; confirm native window minimum dimensions permit the 50% size;
- right-click menu opens in reserved transparent space above and to the right of the subject, never over the character; closing it restores the pet window without moving the character's bottom-right screen anchor;
- work starts from real input, not merely opening a file;
- coding pause, work completion, task success/failure and debugger transitions;
- new message interrupts any state and returns to the latest valid base state;
- repeated polling of the same state does not restart its APNG;
- every state renders without a CSS/image-generated floor shadow or character `drop-shadow`;
- no CPU-heavy high-frequency scan.

On macOS, separately verify the native foreground/activity adapter, Accessibility consent behavior, launch-at-login implementation and every trigger documented for the Mac build. Do not infer that a Windows hook works on macOS because the shared UI compiled.

Success: visual interaction and the requested platform's native signals behave as specified.

## Phase 7 — build the release

Before any release build, complete a new final review of the exact encoded assets and native runtime being shipped. Write `output/reviews/release-quality-decision.json` for the current version with all 13 states and every required check in `references/quality-and-delivery.md`. This is required on every Skill run; prior-version approval cannot be reused. The build scripts reject a missing, stale or failed decision.

For Windows, run on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File <skill>/scripts/build_release.ps1 `
  -ProjectPath <project>
```

The script rejects the bundled generic chibi placeholder, then runs frontend build, Rust tests and Tauri NSIS packaging, copies the installer and user guides into a release directory, and reports bytes and SHA256.

For macOS, run on a Mac:

```bash
python <skill>/scripts/build_release_macos.py \
  --project <project>
```

The macOS script rejects the bundled generic chibi placeholder and builds `.app` and DMG artifacts. A shareable release requires Developer ID signing and notarization credentials; use `--allow-unsigned` only for an explicitly requested local test and label it as unsigned. Windows cannot produce or validate the final Mac bundle. When both platforms are requested, reuse the approved visual assets and user-specific icon but run and verify each native build on its own OS.

Do not run either desktop release path for iOS/iPadOS. Do not copy the source photo, chroma masters, generations, key poses, frames or review sheets into an installer folder. Do not sign, notarize, upload or publish without explicit authorization.

Success: each requested release folder contains its native installer, function guide and state/privacy guide.

## Stop and report conditions

Stop rather than fabricate success when:

- the subject is ambiguous;
- ImageGen is unavailable and the user has not approved its fallback;
- the Skill runs outside Codex and no external image provider/API is configured and approved;
- true native transparency is needed and fallback permission is absent;
- identity drift or anatomy defects persist after focused iterations;
- animation stability/alpha gates fail;
- the current-version final visual review is missing or reports ghosting, shaking/bobbing, irregular scaling, cropping, discontinuity, deformation/fragments or character/floor shadows;
- the user's standing-base program icon is missing, clipped, unreadable at small sizes or not marked ready;
- the requested platform does not match the available template/toolchain;
- the requested OS/Rust/Node/native toolchain cannot build its installer;
- macOS runtime parity is claimed while native triggers remain unimplemented or untested;
- antivirus, signing or external publishing requires new authorization.

Preserve completed artifacts and state the exact blocking gate and next action.

## Final handoff

Lead with the platform-appropriate result. For Windows, provide the NSIS installer and SmartScreen/signing status. For macOS, provide the DMG and optional `.app`, architecture, Developer ID/signing/notarization status and any permission-dependent trigger limitations. For both, provide separate release folders and hashes. Always include the program-icon review, user guide, privacy/state guide, source project, selected image provider/model, built-in versus external mode, the current-version release-quality decision and passed gates. For iOS/iPadOS, distinguish a reusable animation asset pack from a signed app or `.ipa`; never claim a desktop installer is compatible.
