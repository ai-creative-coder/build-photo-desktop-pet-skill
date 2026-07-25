# Quality gates and delivery

## Contents

1. Gate sequence
2. Frame and alpha checks
3. Runtime checks
4. Windows packaging
5. macOS packaging
6. Handoff contract
7. Reusable-skill privacy audit

## 1. Gate sequence

Do not batch the next phase while the current phase has unresolved structural defects.

### Gate A — source and character

- intended subject is unambiguous;
- character bible exists;
- base chibi identity, clothing and shoes match visible source evidence;
- human/upright base is `2.6–2.7` heads unless the user approved another ratio; natural animals use a recorded species-appropriate chibi ratio;
- a saved landmark report and overlay prove the upright base is `2.6–2.7` heads and `37–39%` head fraction; prompt wording and visual impression alone do not pass;
- base hands/paws/wings are complete and relaxed, with no removed-object gripping pose;
- handheld/carried objects, unwanted straps, scene props, text, logos, watermarks, effects, floor shadows and reflections are absent from the neutral base;
- inferred occluded anatomy or clothing is minimal and recorded;
- full body and fine extremities are not cropped;
- chroma-key and RGBA base masters both exist and share the same geometry;
- RGBA corners are transparent, visible key-color residue is zero, and checker/white/dark composites pass;
- front/side/back/three-quarter turnaround is internally consistent.
- the approved neutral standing RGBA base is frozen as the only program-icon subject source.

### Gate B — state stills

- all 13 states exist under stable state names;
- every state has a saved semantic motion plan with at least two declared expression/joint/prop changes and a trigger mapping;
- anatomy and real-world prop logic pass visual inspection;
- every still is RGBA with transparent corners;
- every still is free of floor planes, cast/contact shadows and reflections, including beneath furniture;
- hair/fur/feathers, fingers/paws, thin accessories and enclosed spaces pass checker/white/dark review.

### Gate C — representative motion proof

Before expensive batch animation, finish thinking and coding as proof states. Thinking tests face/eye/icon separation. Coding tests full-scene stability, anatomy-appropriate input key poses and screen masking. If either shakes, scales, warps or contains fragments, fix the production method before continuing.

When the user explicitly requests autonomous completion, continue only after both proof states pass automated and visual review. Otherwise show them for confirmation.

### Gate D — all animations

- exactly 12 frames each;
- all canvases `384x341 RGBA`;
- one shared uniform transform per state;
- one declared stable subject-scale landmark per state, measured from decoded clean key poses, with at most 1 px height range or 2 px width range;
- non-locomotion sole/table baselines drift exactly 0 px; any documented locomotion exception is at most 1 px;
- declared static scene pixels do not change;
- whole-subject bobbing, sinusoidal scaling, camera wobble and one-pixel uniqueness hacks are absent;
- generated pixels and runtime CSS contain no floor/ground oval, character drop-shadow, contact shadow or reflection;
- no frame cross-dissolves two complete characters/scenes; intentional hold frames contain one clean pose only;
- coding uses an over-the-shoulder/rear three-quarter view where the character faces the monitor, both typing hands are readable and changing data is on the visible monitor front;
- no unknown connected components or border fragments;
- effect/subject overlap is zero unless deliberately attached;
- storyboard, onion-skin and enlarged face/moving-extremity audits exist.

### Gate E — encoded assets

- APNG/WebP decode successfully;
- APNG decodes to exactly 12 frames;
- each decoded APNG frame is pixel-identical to its source PNG;
- intentional duplicate hold frames remain explicit in the APNG timeline, with full-frame source blending and no encoder-generated residual image;
- no residual frame, vanished base layer or rectangle artifact;
- actual-size loop looks stable and the last frame returns naturally to the first.

### Mandatory current-release visual decision

After encoding and native runtime testing, visually review the exact 13 assets and application version that will ship. Automated metrics support this review but never replace actual-size playback, slow stepping and enlarged face/hand/prop inspection. Do not reuse an earlier version's decision.

Write `output/reviews/release-quality-decision.json` with:

```json
{
  "ok": true,
  "version": "1.0.0",
  "states_reviewed": [
    "idle", "click", "drag", "stretch", "thinking", "coding",
    "processing", "debugging", "error", "drink-water",
    "task-complete", "new-message", "break-reminder"
  ],
  "checks": {
    "no_ghosting": true,
    "no_shaking_or_bobbing": true,
    "no_irregular_scaling": true,
    "no_action_cropping": true,
    "continuous_motion": true,
    "no_deformation_or_fragments": true,
    "no_floor_or_character_drop_shadow": true,
    "actual_size_loop_reviewed": true,
    "native_runtime_reviewed": true
  }
}
```

Set `ok: false` when any state shows residual/double characters, root shaking, unexplained bobbing, irregular scale breathing, clipped hair/hands/props, discontinuous action, broken anatomy, warped furniture, fragments, floor/contact shadows or runtime drop-shadows. Repair, re-encode and repeat the full current-release review before changing it to true. `validate_release_review.py` and both release builders must reject a missing, stale or incomplete decision.

### Gate F — application and installer

- final 13-name asset contract passes `validate_pet_assets.py`;
- project-specific PNG, ICO and ICNS icons were generated from the current user's approved standing base;
- icon review at 256/128/64/32 px shows readable identity, complete silhouette, stable proportions and no clipping;
- `project-spec.json` marks `custom_icon_ready: true`; the bundled generic chibi placeholder is not shipped;
- frontend build and Rust tests pass;
- transparent always-on-top window appears at bottom-right without console;
- click, real drag, right-click, size, tray, autostart and exit work;
- drag begins at 7 px, visibly communicates effort/cheering and encouragement, remains active during movement and does not restart on release;
- no state has a character/floor shadow in generated pixels or runtime CSS;
- automatic state transitions and highest-priority message restoration work;
- each requested platform passes its native runtime acceptance;
- each requested platform's installer, usage guide and privacy/state guide are in one release folder.

## 2. Frame and alpha checks

Use `scripts/make_animation.py` after producing precomposited frames:

```powershell
python scripts/make_animation.py `
  --frames-dir <state>\frames_alpha `
  --out-dir <state>\export `
  --asset-name thinking `
  --frame-ms 180
```

Review `validation.json`. Automated lower-anchor metrics are advisory for scenes with furniture. Visual multi-anchor review remains required.

Do not consider fixed canvas dimensions proof of stability. Compare contact/table baseline, body center, limb roots, head, furniture and monitor. Inspect frame transitions 4→5 and 8→9 when any storyboard source was involved.

Do not consider a fixed full-alpha height proof of stable character scale. The release review must record a decoded subject-scale landmark that excludes detached props/effects and changing action extents. Fail before integration when its three clean key-pose measurements exceed a 1 px height range or a 2 px width range.

For alpha fringe, inspect all translucent pixels. Keep opaque pixels unchanged. Reconstruct polluted edge RGB from nearby higher-alpha clean pixels. Do not propagate a contaminated neighbor and do not globally reduce alpha.

## 3. Runtime checks

Use browser preview for fast state-by-state review, then test the native Tauri build. The browser cannot prove OS hooks, window movement, notification/accessibility permission, tray or autostart.

Test:

- repeated click restarts greeting at frame 1;
- press/release without movement is click, not drag;
- drag changes real window coordinates;
- random preview plays one cycle and yields to detected state;
- same detected state does not restart repeatedly;
- real typing in a recognized coding context activates coding; a pause over 30 s activates thinking; task/debugger signals activate their matching motion;
- a message interrupts work and returns to the latest work state;
- bubble stays top-right and scales with the pet;
- native scale limits and window minimum size allow 50%, 85% and 100% exactly, and the visible `384x341` character viewport—not only the native window—matches the selected percentage;
- the right-click menu opens above and to the right of the subject in reserved transparent space at 50%, 85% and 100%, never covers the character, preserves the character's bottom-right screen anchor and restores the original window size on close;
- the current-version `release-quality-decision.json` passes `scripts/validate_release_review.py`;
- 15/50/60-minute timers and 5/10-minute resets are logically separate.

On Windows, verify foreground-window/process classification, keyboard-activity metadata, Windows notification access and registry autostart. On macOS, verify the implemented macOS activity adapter, Accessibility permission behavior, foreground application classification, login-item behavior and every trigger claimed in the bundled guide. Do not advertise a macOS trigger that only has a Windows implementation.

## 4. Windows packaging

The bundled template uses React, TypeScript, Vite, Tauri 2 and Rust. It builds a current-user NSIS installer with LZMA compression and WebView2 bootstrap. Release profile uses size optimization, LTO, one codegen unit, panic abort and symbol stripping.

Scaffold:

```powershell
python <skill>\scripts\new_project.py `
  --out <workspace> `
  --product-name "我的桌宠" `
  --slug my-photo-pet `
  --version 1.0.0
```

Copy the final 13 animated assets into `public/assets/pet/integrated-v1`, validate them, then build:

```powershell
python <skill>\scripts\generate_project_icons.py `
  --source <approved-standing-alpha.png> `
  --project <workspace>
python <skill>\scripts\validate_pet_assets.py <workspace>\public\assets\pet\integrated-v1
powershell -ExecutionPolicy Bypass -File <skill>\scripts\build_release.ps1 -ProjectPath <workspace>
```

The packaged runtime must contain only one active 13-state asset set. If historical sets remain under `public/`, give every active runtime file a release-qualified, globally unique basename as well as a versioned directory, and update the runtime mapping accordingly. Reusing names such as `idle.png` or `break-reminder.png` across retained sets can cause a native build to serve a stale embedded resource.

Never include the current user's source photo, discarded generations, key poses or review sheets in the installer. Keep them in that user's private project output only. Never include any user source or derived subject asset in this reusable skill package. The release folder should contain the installer and two user-facing guides.

## 5. macOS packaging

Build macOS artifacts only on macOS with Xcode Command Line Tools, Node.js and Rust installed. The generic project uses Tauri's platform-specific `tauri.macos.conf.json` and produces an `.app` plus a DMG.

```bash
python <skill>/scripts/generate_project_icons.py \
  --source <approved-standing-alpha.png> \
  --project <workspace>
python <skill>/scripts/build_release_macos.py \
  --project <workspace>
```

For a local test build without Apple distribution credentials, explicitly add `--allow-unsigned` and label the result as unsigned/not notarized. For a shareable release, provide a `Developer ID Application` signing identity and Apple notarization credentials through the supported Tauri environment variables. Do not put secrets in the project, Skill or release folder.

The macOS release script must run frontend build, Rust tests, Tauri `app,dmg` bundling, signature verification and Gatekeeper/stapler checks when signing is required. Build and report the current architecture (`arm64` or `x86_64`). Do not call a single-architecture build universal; create and test a universal binary separately when requested.

Before packaging, replace Windows-only native fallbacks with a tested macOS activity adapter or explicitly remove unsupported automatic triggers from the macOS guide. System-wide keyboard/activity observation may require Accessibility consent. Other apps' notification content or Notification Center database must not be scraped. Use public APIs and metadata-only observation, and keep the app functional when permission is declined.

Copy only the DMG, optional `.app`, and the two user-facing guides into the macOS release folder. Keep source photos, chroma masters, generated frames and review artifacts outside it.

## 6. Handoff contract

Report:

- final release directory and installer path for each requested platform;
- installer bytes and SHA256;
- product/version, OS, architecture, signing and notarization status;
- whether ImageGen used built-in mode or an explicitly approved fallback;
- which gates passed and any remaining limitations;
- notification permission/privacy behavior;
- project source and animation-review locations.
- program-icon review location and confirmation that the icon came from the approved standing base.

Do not claim “works on any computer.” State the tested target. Unsigned Windows installers may show SmartScreen; unsigned or unnotarized macOS builds may be blocked by Gatekeeper. Do not sign, notarize, upload or publish externally without explicit authorization.

## 7. Reusable-skill privacy audit

Before publishing or sharing this skill, run `scripts/audit_skill_privacy.py` against both the source directory and the final ZIP. Supply project-specific names and path fragments through repeated `--forbid` arguments at audit time; never store those private terms in the reusable skill.

The audit must pass with only the three explicitly authorized generic chibi placeholder application icons (`PNG`, `ICO`, `ICNS`) listed as raster files. These three derived icons exist only so the generic template is structurally valid and must be replaced per generated project. Do not bundle the original placeholder source file or its local path. A reusable skill must not contain any other user's source photo, generated subject, project/program icon, animation frame, storyboard, appearance prompt, local source path, camera filename, project name or derived visual asset. Never use the placeholder character as a tutorial example, fallback, identity reference, style reference or proportion reference.

```powershell
python <skill>\scripts\audit_skill_privacy.py <skill> `
  --zip <skill-package.zip> `
  --forbid <private-project-term>
```
