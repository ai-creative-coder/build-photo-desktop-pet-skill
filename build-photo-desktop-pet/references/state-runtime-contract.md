# State and runtime contract

## Contents

1. Final asset names
2. Thirteen states
3. Priority and restoration
4. Work-session inference
5. Notifications and privacy
6. Interaction and UI

## 1. Final asset names

Place these animated assets in `public/assets/pet/integrated-v1`:

```text
idle.png
click.png
drag.png
stretch.png
thinking.png
coding.png
processing.png
debugging.png
error.png
drink-water.png
task-complete.png
new-message.png
break-reminder.png
```

Each file must decode to exactly 12 RGBA frames on a `384x341` canvas.

## 2. Thirteen states

| State | Motion | Trigger | Exit |
|---|---|---|---|
| Idle/resting | blink, gaze and tiny expression/hair-tip settle; fixed root and sole baseline | no stronger state | loop |
| Click greeting | happy wave | click with movement under 7 px | one 1.68 s cycle |
| Drag cheer | determined effort/cheer pose followed by smile, wink, fist/thumbs-up or celebratory effect | pointer/window movement reaches 7 px | remain active while dragging, then settle without restarting frame 1 |
| Stretch | stand and stretch | 15 min without pet click/drag | one 2.16 s cycle |
| Thinking | happy thinking, blink, small icon float | real typing in document/chat/design, or coding pause over 30 s | while work session remains valid |
| Coding | rear/over-shoulder view with alternating typing hands and changing data on the visible monitor front | real typing in supported coding context | pause over 30 s becomes thinking |
| Processing | spinner/progress scan | tracked task is alive | success or failure event |
| Debugging | attentive expression, magnifier, question mark | debugger plus coding context | debugger exits |
| Error | full-body worried/surprised reaction | tracked process exits nonzero or failure event | one 3.84 s cycle |
| Drink water | cup bubbles/water highlight | 60 min active without 5 min away | one 4.2 s cycle and reset |
| Task complete | check and phased stars | task exits zero or valid work session ends | one 3.6 s cycle |
| New message | lively greeting/bell alert | authorized notification or supported observable message signal | one 3.48 s cycle |
| Break reminder | whole-body response to clock | 50 min active without 5 min away | one 4.32 s cycle and reset |

Do not add an “off work” state unless the user explicitly requests it.

## 3. Priority and restoration

```text
new message 150
drag 130
click 125
error 110
task complete 100
drink/break 85
stretch 80
debugging 70
coding 65
processing 60
thinking 50
idle 10
```

Keep the base work state updating while a temporary animation plays. When the temporary animation ends, restore the newest still-valid base state, not a captured old state and not unconditional idle. New message is the highest immediate interrupt.

Do not reload an APNG when repeated polling returns the same state. Repeated reloads restart frame 1 and make the pet look broken.

## 4. Work-session inference

Do not claim semantic understanding of the screen. Use explainable local signals:

- foreground application category;
- occurrence and time of keyboard input, never key values;
- foreground context changes and idle duration;
- tracked process lifetime and exit code;
- debugger processes;
- notification metadata and limited window geometry/unread markers.

Opening a file, focusing a window or clicking does not start work. Real keyboard activity in a recognized work context starts a session. Keep coding during pauses up to 30 s; use thinking for longer pauses while the same work context remains active. End immediately after switching to a non-work context on the next low-frequency poll, or after 10 min system idle. Do not play completion for sessions under 15 s.

Recognize current AI coding tools by process and explicit browser context, including Codex/ChatGPT, Claude Code, Hermes AI, Gemini CLI, Copilot CLI, OpenClaw, OpenCode, Cline, Roo Code, Continue, VS Code, Cursor, TRAE, Windsurf, Kiro, Antigravity, Goose, Aider, Augment, Qoder, CodeBuddy, MarsCode, Tabnine, Codeium/Cody, Visual Studio, JetBrains and terminals. Keep lists maintainable; product processes change over time and must be verified locally.

## 5. Notifications and privacy

On Windows, use `UserNotificationListener` only after explicit system access. Compare source, notification ID and creation time. Do not read sender, title, body or attachments.

Use observable compatibility signals only for allowlisted communication processes: a newly shown compact top-right/bottom-right popup and limited unread-state marker changes. A running IM process alone is not a new message. If an app exposes no notification, popup or unread marker, report that no reliable signal exists and offer the `pet-motion: new-message` integration event.

Keep all processing local. Never read or upload code, document text, chat content, clipboard, screen pixels or concrete key values.

## 6. Interaction and UI

Distinguish click from drag by real physical movement. Record pointer and window coordinates on press; capture the pointer; begin moving and play drag only after 7 px; use DPI conversion and `requestAnimationFrame` to coalesce position writes. Ensure Tauri grants `core:window:allow-set-position`.

At the 7 px threshold, immediately enter `drag` and keep that state active for the whole drag. On release, finish the current encouragement motion without reloading its APNG. The visual and message must clearly communicate cheering/encouragement, not a neutral pose or unrelated movement.

Random state is a one-cycle preview, not a persistent override. Right-click settings should provide random preview, notification access, autostart, size and exit. Keep the usage guide beside the installer, not in the pet menu.

Treat message reminders as a persistent application preference separate from operating-system notification permission. The menu item must remain interactive after system access is allowed and must switch between localized equivalents of “message reminders: on” and “message reminders: off” in the confirmed language. While disabled, ignore incoming notification/popup sequence changes and advance the stored sequence so re-enabling does not replay messages received while disabled. Request system access only when needed for the enabled path; other interactions must remain usable when access is denied or unavailable.

Place reminder bubbles in a fixed UI container at top-right (`top:8px; right:8px`). Do not position them from per-frame alpha bounds. Apply one `--pet-ui-scale` directly to the `384x341` character viewport and to bubble typography, padding, border, radius and shadow; shrinking only the native window is not proof that the character itself reached the selected scale. The supported range is 50%–100% with 85% default. Test 50%, 85% and 100% without covering the face, and set native minimum window dimensions to the 50% size so the operating system does not silently clamp it.

The right-click menu must appear in reserved transparent space above and to the right of the character, never over the subject. Temporarily expand the native transparent window upward while keeping its bottom-right screen anchor fixed, render the menu at the reserved area's top-right, hide any speech bubble while the menu is open, and restore the original pet window size when it closes. Keep the menu readable at 50% instead of scaling it down with the pet.

When a pointer press on the pet closes the menu and immediately begins a drag, await the native resize/position result and rebase the drag origin to that returned physical window position before applying any pointer delta. Do not move from a cached pre-close top-left coordinate. The first post-menu drag must preserve the character's screen anchor and follow only the user's actual pointer displacement.

Do not render a floor/ground oval, character `drop-shadow`, contact shadow or reflection beneath any state. Keep menu and speech-bubble shadows only when needed for UI readability; they must not appear under the character.

Use these confirmed strings only when the selected locale is Simplified Chinese; translate their meaning naturally for every other confirmed language:

- click: `你好呀！又是元气满满的一天。`
- drag: `今天也要加油呀！`
- coding title/body: `编码中` / `稍等一会，正在飞速编码中`

Do not show a permanent bottom status caption or a six-dot drag handle.
