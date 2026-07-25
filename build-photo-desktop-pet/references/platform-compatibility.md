# Platform compatibility

## Windows

The bundled runtime template targets Windows x64 and produces a current-user NSIS `.exe`. It uses Windows-specific foreground-window, process, notification, registry autostart and transparent always-on-top window behavior.

Do not present this `.exe`, its Rust Windows hooks or `build_release.ps1` as portable to iOS, iPadOS or macOS.

Build on Windows with `scripts/build_release.ps1`. Report x64, signing and SmartScreen status.

## macOS

The shared visual assets and Tauri UI can produce a macOS `.app` and DMG, but the build must run on a Mac. Tauri automatically merges `src-tauri/tauri.macos.conf.json`; build with `scripts/build_release_macos.py`. A Windows host cannot create or validate the final macOS bundle. See Tauri's [macOS application bundle](https://v2.tauri.app/distribute/macos-application-bundle/) and [platform-specific configuration](https://v2.tauri.app/develop/configuration-files/).

Treat packaging and native behavior as separate gates:

1. Keep shared click, drag, size, tray, animation and window behavior.
2. Implement and test a macOS activity adapter before claiming automatic work states. Use public APIs, process metadata and no key contents.
3. Request Accessibility consent only when a claimed feature requires trusted event observation. Check trust with Apple's [`AXIsProcessTrustedWithOptions`](https://developer.apple.com/documentation/applicationservices/1459186-axisprocesstrustedwithoptions) and explain the exact benefit before prompting. Declining permission must leave manual interaction and timer states usable.
4. Implement launch-at-login with Apple's [`SMAppService`](https://developer.apple.com/documentation/servicemanagement/smappservice) where supported; do not reuse Windows registry code.
5. Do not scrape another app's content or the Notification Center database. Generic third-party IM notification interception is not equivalent to the Windows listener and must be marked unsupported unless a public, consented integration is implemented.
6. Make the bundled state/privacy guide match the triggers that actually pass on macOS.

For local testing, an unsigned build may be produced only when explicitly requested and must be labeled. For distribution to other Macs, use a `Developer ID Application` identity, hardened runtime and notarization. Tauri supports signing/notarization environment variables; Apple requires suitable signing before notarization and recommends stapling the returned ticket. See [Tauri macOS signing](https://v2.tauri.app/distribute/sign/macos/) and Apple's [notarization documentation](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).

Report the built architecture. An Apple Silicon `arm64` DMG is not automatically an Intel `x86_64` or universal build.

## iPhone and iPad (asset workflow only; separate app required)

An iOS/iPadOS deliverable is a separately built and signed app, commonly distributed through TestFlight/App Store or exported as a signed `.ipa` for eligible registered devices. It requires an Apple App ID, signing certificate, provisioning profile and an Xcode archive/export workflow. See Apple's [distribution documentation](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases/) and [registered-device export documentation](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices).

The current Windows output is incompatible for four independent reasons:

1. NSIS `.exe` is a Windows installer, not an iOS app package.
2. Windows process/window hooks, notification listener and registry autostart APIs do not exist on iOS.
3. iOS normally suspends background apps and only permits declared, limited background modes; it cannot continuously run the Windows observation loop. See Apple's [background execution modes](https://developer.apple.com/documentation/xcode/configuring-background-execution-modes).
4. A normal iOS app cannot behave as a free-floating always-on-top window over arbitrary other apps. Redesign the experience as an in-app companion, Home/Lock Screen widget, Live Activity, notification or App Intent interaction. Widget and Live Activity code runs under system-controlled rendering/update rules; see [WidgetKit](https://developer.apple.com/documentation/WidgetKit) and [widget/Live Activity interactivity](https://developer.apple.com/documentation/WidgetKit/Adding-interactivity-to-widgets-and-Live-Activities).

The visual asset pack remains reusable. Prefer individual RGBA PNG frames or sprite atlases as the portable source of truth. Re-encode animation for the chosen iOS renderer only after testing it in the native app.

If the user asks for iOS:

1. Ask whether they mean iPhone/iPad or macOS if the word “Apple desktop” is ambiguous.
2. Continue character, state and frame asset production.
3. Do not run the Windows scaffold or release script.
4. Require macOS with Xcode for a signed device/App Store build. Tauri also exposes a platform-specific `ios build`, but signing and distribution remain separate; see [Tauri distribution](https://v2.tauri.app/distribute/).
5. Redesign state triggers around app-local activity, explicit user actions, notifications the app owns, widgets and Live Activities. Do not claim access to other apps' processes, typing, messages or foreground state.
6. Report asset-pack completion separately from iOS application/`.ipa` completion.
