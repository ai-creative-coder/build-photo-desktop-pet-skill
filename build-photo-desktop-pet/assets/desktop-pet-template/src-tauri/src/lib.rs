use serde::Serialize;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, LogicalSize, Manager, PhysicalPosition, WebviewWindow,
    WebviewWindowBuilder,
};

#[cfg(windows)]
use std::{
    collections::{HashMap, HashSet},
    mem::size_of,
    ptr::null_mut,
    sync::{
        atomic::{AtomicIsize, AtomicU64, Ordering},
        Mutex, OnceLock,
    },
};

const BASE_WINDOW_WIDTH: f64 = 420.0;
const BASE_WINDOW_HEIGHT: f64 = 410.0;
const CONTEXT_MENU_MIN_WIDTH: f64 = 224.0;
const CONTEXT_MENU_HEIGHT: f64 = 292.0;
const DEFAULT_PET_SCALE: u16 = 85;
const MIN_PET_SCALE: u16 = 50;
const MAX_PET_SCALE: u16 = 100;
const SCREEN_EDGE_GAP: i32 = 14;

#[cfg(windows)]
const AUTO_START_PREFERENCE_KEY: &str = "Software\\__REGISTRY_KEY__";
#[cfg(windows)]
const AUTO_START_RUN_KEY: &str = "Software\\Microsoft\\Windows\\CurrentVersion\\Run";
#[cfg(windows)]
const AUTO_START_VALUE_NAME: &str = "__REGISTRY_KEY__";

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SystemActivitySnapshot {
    idle_seconds: u64,
    keyboard_idle_seconds: Option<u64>,
    keyboard_sequence: u64,
    foreground_process: String,
    foreground_kind: String,
    debugger_running: bool,
    task_process_running: bool,
    finished_task_succeeded: Option<bool>,
    notification_access: String,
    message_signal_sequence: u64,
}

#[cfg(windows)]
static TRACKED_TASKS: OnceLock<Mutex<HashMap<u32, isize>>> = OnceLock::new();

#[cfg(windows)]
static LAST_KEYBOARD_INPUT_TICK: AtomicU64 = AtomicU64::new(0);

#[cfg(windows)]
static KEYBOARD_SEQUENCE: AtomicU64 = AtomicU64::new(0);

#[cfg(windows)]
static KEYBOARD_HOOK: AtomicIsize = AtomicIsize::new(0);

#[cfg(windows)]
static KNOWN_NOTIFICATIONS: OnceLock<Mutex<Option<HashSet<String>>>> = OnceLock::new();

#[cfg(windows)]
static KNOWN_MESSAGE_POPUPS: OnceLock<Mutex<Option<HashSet<isize>>>> = OnceLock::new();

#[cfg(windows)]
static KNOWN_MESSAGE_BADGES: OnceLock<Mutex<Option<HashSet<String>>>> = OnceLock::new();

#[cfg(windows)]
static MESSAGE_PROCESS_IDS: OnceLock<Mutex<HashSet<u32>>> = OnceLock::new();

#[cfg(windows)]
static MESSAGE_POPUP_SEQUENCE: AtomicU64 = AtomicU64::new(0);

#[cfg(windows)]
static MESSAGE_SIGNAL_SEQUENCE: AtomicU64 = AtomicU64::new(0);

#[cfg(windows)]
static REPORTED_MESSAGE_POPUP_SEQUENCE: AtomicU64 = AtomicU64::new(0);

#[cfg(windows)]
static MESSAGE_WINDOW_HOOK: AtomicIsize = AtomicIsize::new(0);

#[cfg(windows)]
const LEGACY_MESSAGE_PROCESSES: &[&str] = &[
    "wechat.exe",
    "weixin.exe",
    "wechatappex.exe",
    "qq.exe",
    "qqnt.exe",
    "tim.exe",
    "wxwork.exe",
    "wxworkweb.exe",
    "wecom.exe",
    "dingtalk.exe",
    "dingtalkmain.exe",
    "dingtalklauncher.exe",
    "feishu.exe",
    "lark.exe",
    "slack.exe",
    "teams.exe",
    "ms-teams.exe",
    "discord.exe",
    "telegram.exe",
    "outlook.exe",
    "olk.exe",
    "foxmail.exe",
    "mailbird.exe",
    "emclient.exe",
    "mailspring.exe",
    "postbox.exe",
    "thunderbird.exe",
    "hxtsr.exe",
    "whatsapp.exe",
    "signal.exe",
    "line.exe",
    "kakaotalk.exe",
    "messenger.exe",
    "viber.exe",
    "skype.exe",
];

#[cfg(windows)]
const DEBUGGER_PROCESSES: &[&str] = &[
    "debugpy.exe",
    "gdb.exe",
    "lldb.exe",
    "vsdbg.exe",
    "cdb.exe",
    "windbg.exe",
    "java-debug.exe",
];

#[cfg(windows)]
const TASK_PROCESSES: &[&str] = &[
    "msbuild.exe",
    "vstest.console.exe",
    "cargo.exe",
    "rustc.exe",
    "cmake.exe",
    "ninja.exe",
    "gradle.exe",
    "gradlew.exe",
    "mvn.exe",
    "ffmpeg.exe",
    "7z.exe",
    "7zg.exe",
    "winrar.exe",
];

#[cfg(windows)]
fn primary_work_area() -> Option<(i32, i32, i32, i32)> {
    use std::ffi::c_void;
    use windows_sys::Win32::{
        Foundation::RECT,
        UI::WindowsAndMessaging::{SystemParametersInfoW, SPI_GETWORKAREA},
    };

    let mut rect = RECT {
        left: 0,
        top: 0,
        right: 0,
        bottom: 0,
    };
    let ok = unsafe {
        SystemParametersInfoW(SPI_GETWORKAREA, 0, &mut rect as *mut RECT as *mut c_void, 0)
    };
    (ok != 0).then_some((rect.left, rect.top, rect.right, rect.bottom))
}

#[cfg(not(windows))]
fn primary_work_area() -> Option<(i32, i32, i32, i32)> {
    None
}

fn position_bottom_right(window: &WebviewWindow) -> Result<(), String> {
    let window_size = window.outer_size().map_err(|error| error.to_string())?;
    let (left, top, right, bottom) = if let Some(area) = primary_work_area() {
        area
    } else {
        let monitor = window
            .current_monitor()
            .map_err(|error| error.to_string())?
            .ok_or_else(|| "未找到可用显示器".to_string())?;
        let position = monitor.position();
        let size = monitor.size();
        (
            position.x,
            position.y,
            position.x + size.width as i32,
            position.y + size.height as i32,
        )
    };
    let x = (right - window_size.width as i32 - SCREEN_EDGE_GAP).max(left);
    let y = (bottom - window_size.height as i32 - SCREEN_EDGE_GAP).max(top);
    window
        .set_position(PhysicalPosition::new(x, y))
        .map_err(|error| error.to_string())
}

fn clamp_pet_scale(scale: u16) -> u16 {
    scale.clamp(MIN_PET_SCALE, MAX_PET_SCALE)
}

fn read_saved_pet_scale(app: &AppHandle) -> u16 {
    let Ok(data_dir) = app.path().app_local_data_dir() else {
        return DEFAULT_PET_SCALE;
    };
    std::fs::read_to_string(data_dir.join("pet-scale.txt"))
        .ok()
        .and_then(|saved| saved.trim().parse::<u16>().ok())
        .map(clamp_pet_scale)
        .unwrap_or(DEFAULT_PET_SCALE)
}

fn save_pet_scale(app: &AppHandle, scale: u16) -> Result<(), String> {
    let data_dir = app
        .path()
        .app_local_data_dir()
        .map_err(|error| error.to_string())?;
    std::fs::create_dir_all(&data_dir).map_err(|error| error.to_string())?;
    std::fs::write(data_dir.join("pet-scale.txt"), scale.to_string())
        .map_err(|error| error.to_string())
}

fn pet_window_dimensions(scale: u16, context_menu_open: bool) -> (f64, f64) {
    let safe_scale = clamp_pet_scale(scale);
    let ratio = f64::from(safe_scale) / 100.0;
    let pet_width = (BASE_WINDOW_WIDTH * ratio).round();
    let pet_height = (BASE_WINDOW_HEIGHT * ratio).round();
    if context_menu_open {
        (pet_width.max(CONTEXT_MENU_MIN_WIDTH), pet_height + CONTEXT_MENU_HEIGHT)
    } else {
        (pet_width, pet_height)
    }
}

fn resize_pet_window(
    window: &WebviewWindow,
    scale: u16,
    context_menu_open: bool,
) -> Result<u16, String> {
    let safe_scale = clamp_pet_scale(scale);
    let (width, height) = pet_window_dimensions(safe_scale, context_menu_open);
    window
        .set_size(LogicalSize::new(width, height))
        .map_err(|error| error.to_string())?;
    Ok(safe_scale)
}

#[tauri::command]
fn get_pet_scale(app: AppHandle) -> u16 {
    read_saved_pet_scale(&app)
}

#[tauri::command]
fn set_pet_scale(app: AppHandle, scale: u16, context_menu_open: bool) -> Result<u16, String> {
    let window = app
        .get_webview_window("main")
        .ok_or_else(|| "未找到桌宠窗口".to_string())?;
    let safe_scale = resize_pet_window(&window, scale, context_menu_open)?;
    position_bottom_right(&window)?;
    save_pet_scale(&app, safe_scale)?;
    Ok(safe_scale)
}

#[tauri::command]
fn set_context_menu_open(app: AppHandle, open: bool) -> Result<(), String> {
    let window = app
        .get_webview_window("main")
        .ok_or_else(|| "未找到桌宠窗口".to_string())?;
    let old_position = window.outer_position().map_err(|error| error.to_string())?;
    let old_size = window.outer_size().map_err(|error| error.to_string())?;
    resize_pet_window(&window, read_saved_pet_scale(&app), open)?;
    let new_size = window.outer_size().map_err(|error| error.to_string())?;
    window
        .set_position(PhysicalPosition::new(
            old_position.x + old_size.width as i32 - new_size.width as i32,
            old_position.y + old_size.height as i32 - new_size.height as i32,
        ))
        .map_err(|error| error.to_string())
}

#[tauri::command]
fn position_pet_bottom_right(app: AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("main")
        .ok_or_else(|| "未找到桌宠窗口".to_string())?;
    position_bottom_right(&window)
}

#[tauri::command]
fn quit_app(app: AppHandle) {
    app.exit(0);
}

#[cfg(windows)]
fn wide_null(value: &str) -> Vec<u16> {
    value.encode_utf16().chain(std::iter::once(0)).collect()
}

#[cfg(windows)]
fn auto_start_command(executable: &std::path::Path) -> String {
    format!("\"{}\"", executable.display())
}

#[cfg(windows)]
fn write_registry_dword(path: &str, name: &str, value: u32) -> Result<(), String> {
    use windows_sys::Win32::{
        Foundation::ERROR_SUCCESS,
        System::Registry::{
            RegCloseKey, RegCreateKeyExW, RegSetValueExW, HKEY, HKEY_CURRENT_USER, KEY_SET_VALUE,
            REG_DWORD, REG_OPTION_NON_VOLATILE,
        },
    };

    let path = wide_null(path);
    let name = wide_null(name);
    let mut key: HKEY = null_mut();
    let opened = unsafe {
        RegCreateKeyExW(
            HKEY_CURRENT_USER,
            path.as_ptr(),
            0,
            std::ptr::null(),
            REG_OPTION_NON_VOLATILE,
            KEY_SET_VALUE,
            std::ptr::null(),
            &mut key,
            std::ptr::null_mut(),
        )
    };
    if opened != ERROR_SUCCESS {
        return Err(format!("无法打开开机启动设置，Windows错误码：{opened}"));
    }
    let written = unsafe {
        RegSetValueExW(
            key,
            name.as_ptr(),
            0,
            REG_DWORD,
            &value as *const u32 as *const u8,
            size_of::<u32>() as u32,
        )
    };
    unsafe { RegCloseKey(key) };
    (written == ERROR_SUCCESS)
        .then_some(())
        .ok_or_else(|| format!("无法保存开机启动设置，Windows错误码：{written}"))
}

#[cfg(windows)]
fn read_registry_dword(path: &str, name: &str) -> Result<Option<u32>, String> {
    use windows_sys::Win32::{
        Foundation::{ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND, ERROR_SUCCESS},
        System::Registry::{
            RegCloseKey, RegOpenKeyExW, RegQueryValueExW, HKEY, HKEY_CURRENT_USER, KEY_QUERY_VALUE,
            REG_DWORD,
        },
    };

    let path = wide_null(path);
    let name = wide_null(name);
    let mut key: HKEY = null_mut();
    let opened = unsafe {
        RegOpenKeyExW(
            HKEY_CURRENT_USER,
            path.as_ptr(),
            0,
            KEY_QUERY_VALUE,
            &mut key,
        )
    };
    if opened == ERROR_FILE_NOT_FOUND || opened == ERROR_PATH_NOT_FOUND {
        return Ok(None);
    }
    if opened != ERROR_SUCCESS {
        return Err(format!("无法读取开机启动设置，Windows错误码：{opened}"));
    }

    let mut value = 0u32;
    let mut value_type = 0u32;
    let mut size = size_of::<u32>() as u32;
    let queried = unsafe {
        RegQueryValueExW(
            key,
            name.as_ptr(),
            std::ptr::null(),
            &mut value_type,
            &mut value as *mut u32 as *mut u8,
            &mut size,
        )
    };
    unsafe { RegCloseKey(key) };
    if queried == ERROR_FILE_NOT_FOUND {
        return Ok(None);
    }
    if queried != ERROR_SUCCESS || value_type != REG_DWORD || size != size_of::<u32>() as u32 {
        return Err(format!("开机启动设置格式无效，Windows错误码：{queried}"));
    }
    Ok(Some(value))
}

#[cfg(windows)]
fn write_auto_start_run_entry(enabled: bool) -> Result<(), String> {
    use windows_sys::Win32::{
        Foundation::{ERROR_FILE_NOT_FOUND, ERROR_SUCCESS},
        System::Registry::{
            RegCloseKey, RegCreateKeyExW, RegDeleteValueW, RegSetValueExW, HKEY, HKEY_CURRENT_USER,
            KEY_SET_VALUE, REG_OPTION_NON_VOLATILE, REG_SZ,
        },
    };

    let command = if enabled {
        let executable = std::env::current_exe().map_err(|error| error.to_string())?;
        Some(wide_null(&auto_start_command(&executable)))
    } else {
        None
    };
    let path = wide_null(AUTO_START_RUN_KEY);
    let name = wide_null(AUTO_START_VALUE_NAME);
    let mut key: HKEY = null_mut();
    let opened = unsafe {
        RegCreateKeyExW(
            HKEY_CURRENT_USER,
            path.as_ptr(),
            0,
            std::ptr::null(),
            REG_OPTION_NON_VOLATILE,
            KEY_SET_VALUE,
            std::ptr::null(),
            &mut key,
            std::ptr::null_mut(),
        )
    };
    if opened != ERROR_SUCCESS {
        return Err(format!("无法打开Windows启动项，错误码：{opened}"));
    }

    let changed = if enabled {
        let command = command.as_ref().expect("enabled startup command");
        unsafe {
            RegSetValueExW(
                key,
                name.as_ptr(),
                0,
                REG_SZ,
                command.as_ptr() as *const u8,
                (command.len() * size_of::<u16>()) as u32,
            )
        }
    } else {
        unsafe { RegDeleteValueW(key, name.as_ptr()) }
    };
    unsafe { RegCloseKey(key) };
    if changed == ERROR_SUCCESS || (!enabled && changed == ERROR_FILE_NOT_FOUND) {
        Ok(())
    } else {
        Err(format!("无法更新Windows启动项，错误码：{changed}"))
    }
}

#[cfg(windows)]
fn initialize_auto_start() -> Result<bool, String> {
    if cfg!(debug_assertions) {
        return Ok(true);
    }
    let saved = read_registry_dword(AUTO_START_PREFERENCE_KEY, "AutoStartEnabled")?;
    let enabled = saved.map(|value| value != 0).unwrap_or(true);
    write_auto_start_run_entry(enabled)?;
    if saved.is_none() {
        write_registry_dword(AUTO_START_PREFERENCE_KEY, "AutoStartEnabled", 1)?;
    }
    Ok(enabled)
}

#[cfg(windows)]
#[tauri::command]
fn auto_start_enabled() -> Result<bool, String> {
    if cfg!(debug_assertions) {
        return Ok(true);
    }
    Ok(
        read_registry_dword(AUTO_START_PREFERENCE_KEY, "AutoStartEnabled")?
            .map(|value| value != 0)
            .unwrap_or(false),
    )
}

#[cfg(windows)]
#[tauri::command]
fn set_auto_start(enabled: bool) -> Result<bool, String> {
    if cfg!(debug_assertions) {
        return Ok(enabled);
    }
    write_auto_start_run_entry(enabled)?;
    write_registry_dword(
        AUTO_START_PREFERENCE_KEY,
        "AutoStartEnabled",
        u32::from(enabled),
    )?;
    Ok(enabled)
}

#[cfg(not(windows))]
#[tauri::command]
fn auto_start_enabled() -> Result<bool, String> {
    Ok(false)
}

#[cfg(not(windows))]
#[tauri::command]
fn set_auto_start(_enabled: bool) -> Result<bool, String> {
    Ok(false)
}

#[cfg(windows)]
unsafe extern "system" fn keyboard_hook_callback(
    code: i32,
    wparam: windows_sys::Win32::Foundation::WPARAM,
    lparam: windows_sys::Win32::Foundation::LPARAM,
) -> windows_sys::Win32::Foundation::LRESULT {
    use windows_sys::Win32::{
        System::SystemInformation::GetTickCount64,
        UI::WindowsAndMessaging::{CallNextHookEx, WM_KEYDOWN, WM_SYSKEYDOWN},
    };

    if code >= 0 && (wparam as u32 == WM_KEYDOWN || wparam as u32 == WM_SYSKEYDOWN) {
        LAST_KEYBOARD_INPUT_TICK.store(GetTickCount64(), Ordering::Relaxed);
        KEYBOARD_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    }
    CallNextHookEx(null_mut(), code, wparam, lparam)
}

#[cfg(windows)]
fn install_keyboard_monitor() -> bool {
    use windows_sys::Win32::{
        System::LibraryLoader::GetModuleHandleW,
        UI::WindowsAndMessaging::{SetWindowsHookExW, WH_KEYBOARD_LL},
    };

    let hook = unsafe {
        SetWindowsHookExW(
            WH_KEYBOARD_LL,
            Some(keyboard_hook_callback),
            GetModuleHandleW(std::ptr::null()),
            0,
        )
    };
    if hook.is_null() {
        return false;
    }
    KEYBOARD_HOOK.store(hook as isize, Ordering::Relaxed);
    true
}

#[cfg(windows)]
fn keyboard_activity() -> (Option<u64>, u64) {
    use windows_sys::Win32::System::SystemInformation::GetTickCount64;

    let sequence = KEYBOARD_SEQUENCE.load(Ordering::Relaxed);
    let last_tick = LAST_KEYBOARD_INPUT_TICK.load(Ordering::Relaxed);
    let available = KEYBOARD_HOOK.load(Ordering::Relaxed) != 0;
    let idle_seconds = (available && last_tick != 0)
        .then(|| unsafe { GetTickCount64().saturating_sub(last_tick) / 1000 });
    (idle_seconds, sequence)
}

#[cfg(windows)]
#[tauri::command]
fn system_idle_seconds() -> u64 {
    use std::mem::size_of;
    use windows_sys::Win32::{
        System::SystemInformation::GetTickCount,
        UI::Input::KeyboardAndMouse::{GetLastInputInfo, LASTINPUTINFO},
    };

    let mut info = LASTINPUTINFO {
        cbSize: size_of::<LASTINPUTINFO>() as u32,
        dwTime: 0,
    };
    unsafe {
        if GetLastInputInfo(&mut info) == 0 {
            return 0;
        }
        GetTickCount().wrapping_sub(info.dwTime) as u64 / 1000
    }
}

#[cfg(not(windows))]
#[tauri::command]
fn system_idle_seconds() -> u64 {
    0
}

#[cfg(windows)]
#[tauri::command]
fn foreground_process() -> String {
    use windows_sys::Win32::{
        Foundation::CloseHandle,
        System::Threading::{
            OpenProcess, QueryFullProcessImageNameW, PROCESS_QUERY_LIMITED_INFORMATION,
        },
        UI::WindowsAndMessaging::{GetForegroundWindow, GetWindowThreadProcessId},
    };

    unsafe {
        let window = GetForegroundWindow();
        if window.is_null() {
            return String::new();
        }
        let mut process_id = 0;
        GetWindowThreadProcessId(window, &mut process_id);
        let process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, process_id);
        if process.is_null() {
            return String::new();
        }
        let mut buffer = vec![0u16; 1024];
        let mut length = buffer.len() as u32;
        let ok = QueryFullProcessImageNameW(process, 0, buffer.as_mut_ptr(), &mut length);
        CloseHandle(process);
        if ok == 0 {
            return String::new();
        }
        String::from_utf16_lossy(&buffer[..length as usize])
    }
}

#[cfg(windows)]
fn foreground_window_title() -> String {
    use windows_sys::Win32::UI::WindowsAndMessaging::{
        GetForegroundWindow, GetWindowTextLengthW, GetWindowTextW,
    };

    unsafe {
        let window = GetForegroundWindow();
        if window.is_null() {
            return String::new();
        }
        let length = GetWindowTextLengthW(window);
        if length <= 0 {
            return String::new();
        }
        let mut buffer = vec![0u16; length as usize + 1];
        let copied = GetWindowTextW(window, buffer.as_mut_ptr(), buffer.len() as i32);
        String::from_utf16_lossy(&buffer[..copied.max(0) as usize])
    }
}

#[cfg(windows)]
fn foreground_kind(process_path: &str, window_title: &str) -> &'static str {
    let process = process_path
        .rsplit(['\\', '/'])
        .next()
        .unwrap_or(process_path)
        .to_ascii_lowercase();
    let title = window_title.to_ascii_lowercase();

    const CODING: &[&str] = &[
        "code.exe",
        "cursor.exe",
        "codex.exe",
        "chatgpt.exe",
        "claude.exe",
        "hermes.exe",
        "hermes-ai.exe",
        "hermesagent.exe",
        "gemini.exe",
        "copilot.exe",
        "copilot-cli.exe",
        "opencode.exe",
        "openclaw.exe",
        "cline.exe",
        "roo-code.exe",
        "continue.exe",
        "trae.exe",
        "trae-cn.exe",
        "windsurf.exe",
        "kiro.exe",
        "antigravity.exe",
        "goose.exe",
        "aider.exe",
        "augment.exe",
        "qoder.exe",
        "codebuddy.exe",
        "marscode.exe",
        "tabnine.exe",
        "codeium.exe",
        "cody.exe",
        "warp.exe",
        "devenv.exe",
        "idea64.exe",
        "pycharm64.exe",
        "webstorm64.exe",
        "rider64.exe",
        "clion64.exe",
        "goland64.exe",
        "notepad++.exe",
        "sublime_text.exe",
        "zed.exe",
        "windowsterminal.exe",
        "powershell.exe",
        "pwsh.exe",
    ];
    const WRITING: &[&str] = &[
        "notepad.exe",
        "winword.exe",
        "excel.exe",
        "powerpnt.exe",
        "onenote.exe",
        "obsidian.exe",
        "notion.exe",
        "wps.exe",
        "et.exe",
        "wpp.exe",
        "acrord32.exe",
        "acrobat.exe",
    ];
    const COMMUNICATION: &[&str] = &[
        "teams.exe",
        "ms-teams.exe",
        "slack.exe",
        "wechat.exe",
        "weixin.exe",
        "qq.exe",
        "qqnt.exe",
        "tim.exe",
        "wechatappex.exe",
        "wxwork.exe",
        "wxworkweb.exe",
        "wecom.exe",
        "dingtalk.exe",
        "dingtalkmain.exe",
        "dingtalklauncher.exe",
        "feishu.exe",
        "lark.exe",
        "discord.exe",
        "telegram.exe",
        "zoom.exe",
        "outlook.exe",
        "olk.exe",
        "foxmail.exe",
        "mailbird.exe",
        "emclient.exe",
        "mailspring.exe",
        "postbox.exe",
        "thunderbird.exe",
        "hxtsr.exe",
        "whatsapp.exe",
        "signal.exe",
        "line.exe",
        "kakaotalk.exe",
        "messenger.exe",
        "viber.exe",
        "skype.exe",
    ];
    const CREATIVE: &[&str] = &[
        "figma.exe",
        "mspaint.exe",
        "photoshop.exe",
        "illustrator.exe",
        "blender.exe",
    ];
    const BROWSERS: &[&str] = &[
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "brave.exe",
        "opera.exe",
    ];

    if [
        ".rs", ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".cpp", ".cs", ".go", ".swift", ".kt",
        ".dart", ".php", ".rb", ".vue", ".svelte", ".sql", ".toml", ".yaml", ".yml",
    ]
    .iter()
    .any(|extension| title.contains(extension))
    {
        return "coding";
    }
    if [
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".rtf", ".odt", ".csv",
    ]
    .iter()
    .any(|extension| title.contains(extension))
    {
        return "writing";
    }

    if CODING.contains(&process.as_str()) {
        return "coding";
    }
    if WRITING.contains(&process.as_str()) {
        return "writing";
    }
    if COMMUNICATION.contains(&process.as_str()) {
        return "communication";
    }
    if CREATIVE.contains(&process.as_str()) {
        return "creative";
    }
    if BROWSERS.contains(&process.as_str()) {
        if [
            "codex",
            "chatgpt",
            "claude code",
            "hermes ai",
            "hermes agent",
            "gemini cli",
            "gemini code assist",
            "openclaw",
            "open code",
            "opencode",
            "visual studio code",
            "cursor",
            "trae",
            "windsurf",
            "kiro",
            "antigravity",
            "goose",
            "aider",
            "cline",
            "roo code",
            "continue.dev",
            "augment code",
            "amazon q developer",
            "qoder",
            "codebuddy",
            "marscode",
            "tongyi lingma",
            "通义灵码",
            "lovable",
            "bolt.new",
            "replit",
            "replit agent",
            "v0.dev",
            "devin",
            "manus",
            "firebase studio",
            "google jules",
            "base44",
            "github copilot",
            "github",
            "gitlab",
        ]
        .iter()
        .any(|keyword| title.contains(keyword))
        {
            return "coding";
        }
        if [
            "google docs",
            "腾讯文档",
            "飞书文档",
            "石墨文档",
            "notion",
            "语雀",
            "文档",
        ]
        .iter()
        .any(|keyword| title.contains(keyword))
        {
            return "writing";
        }
        if [
            "slack", "teams", "微信", "discord", "outlook", "gmail", "邮件",
        ]
        .iter()
        .any(|keyword| title.contains(keyword))
        {
            return "communication";
        }
        return "browser";
    }
    "other"
}

#[cfg(windows)]
fn foreground_context() -> (String, String) {
    let process = foreground_process();
    let title = foreground_window_title();
    let kind = foreground_kind(&process, &title).to_string();
    (process, kind)
}

#[cfg(windows)]
fn notification_access_status_value() -> String {
    use windows::UI::Notifications::Management::{
        UserNotificationListener, UserNotificationListenerAccessStatus,
    };

    match UserNotificationListener::Current().and_then(|listener| listener.GetAccessStatus()) {
        Ok(UserNotificationListenerAccessStatus::Allowed) => "allowed",
        Ok(UserNotificationListenerAccessStatus::Denied) => "denied",
        Ok(_) => "unspecified",
        Err(_) => "unavailable",
    }
    .to_string()
}

#[cfg(windows)]
fn is_message_notification_source(source: &str) -> bool {
    let source = source.to_ascii_lowercase();
    [
        "wechat",
        "weixin",
        "微信",
        "wxwork",
        "wecom",
        "企业微信",
        "qq",
        "qqnt",
        "tim",
        "dingtalk",
        "钉钉",
        "feishu",
        "飞书",
        "lark",
        "slack",
        "teams",
        "outlook",
        "mail",
        "邮件",
        "gmail",
        "foxmail",
        "mailbird",
        "em client",
        "mailspring",
        "postbox",
        "discord",
        "telegram",
        "whatsapp",
        "signal",
        "line",
        "kakaotalk",
        "messenger",
        "viber",
        "skype",
    ]
    .iter()
    .any(|keyword| source.contains(keyword))
}

#[cfg(windows)]
fn notification_identity(source: &str, id: u32, created_at: i64) -> String {
    format!("{}|{id}|{created_at}", source.to_ascii_lowercase())
}

#[cfg(windows)]
fn inspect_new_message_notification() -> (String, bool) {
    use windows::UI::Notifications::Management::UserNotificationListenerAccessStatus;
    use windows::UI::Notifications::{Management::UserNotificationListener, NotificationKinds};

    let Ok(listener) = UserNotificationListener::Current() else {
        return ("unavailable".to_string(), false);
    };
    let Ok(status) = listener.GetAccessStatus() else {
        return ("unavailable".to_string(), false);
    };
    if status != UserNotificationListenerAccessStatus::Allowed {
        let label = if status == UserNotificationListenerAccessStatus::Denied {
            "denied"
        } else {
            "unspecified"
        };
        return (label.to_string(), false);
    }
    let Ok(operation) = listener.GetNotificationsAsync(NotificationKinds::Toast) else {
        return ("allowed".to_string(), false);
    };
    let Ok(notifications) = operation.get() else {
        return ("allowed".to_string(), false);
    };

    let mut current_notifications = HashSet::new();
    let mut message_notifications = HashSet::new();
    if let Ok(size) = notifications.Size() {
        for index in 0..size {
            let Ok(notification) = notifications.GetAt(index) else {
                continue;
            };
            let Ok(id) = notification.Id() else { continue };
            let source = notification
                .AppInfo()
                .ok()
                .map(|info| {
                    let model_id = info
                        .AppUserModelId()
                        .map(|value| value.to_string_lossy())
                        .unwrap_or_default();
                    let display_name = info
                        .DisplayInfo()
                        .and_then(|display| display.DisplayName())
                        .map(|value| value.to_string_lossy())
                        .unwrap_or_default();
                    format!("{model_id} {display_name}")
                })
                .unwrap_or_default();
            let created_at = notification
                .CreationTime()
                .map(|value| value.UniversalTime)
                .unwrap_or_default();
            let identity = notification_identity(&source, id, created_at);
            current_notifications.insert(identity.clone());
            if is_message_notification_source(&source) {
                message_notifications.insert(identity);
            }
        }
    }

    let tracker = KNOWN_NOTIFICATIONS.get_or_init(|| Mutex::new(None));
    let Ok(mut known) = tracker.lock() else {
        return ("allowed".to_string(), false);
    };
    let new_message = known
        .as_ref()
        .map(|previous| {
            message_notifications
                .iter()
                .any(|identity| !previous.contains(identity))
        })
        .unwrap_or(false);
    *known = Some(current_notifications);
    ("allowed".to_string(), new_message)
}

#[cfg(windows)]
#[tauri::command]
fn notification_access_status() -> String {
    notification_access_status_value()
}

#[cfg(windows)]
#[tauri::command]
fn request_notification_access() -> Result<String, String> {
    use windows::UI::Notifications::Management::UserNotificationListener;
    let listener = UserNotificationListener::Current().map_err(|error| error.to_string())?;
    let status = listener
        .RequestAccessAsync()
        .and_then(|operation| operation.get())
        .map_err(|error| error.to_string())?;
    if let Some(tracker) = KNOWN_NOTIFICATIONS.get() {
        if let Ok(mut known) = tracker.lock() {
            *known = None;
        }
    }
    Ok(match status.0 {
        1 => "allowed",
        2 => "denied",
        _ => "unspecified",
    }
    .to_string())
}

#[cfg(windows)]
struct MessagePopupScan {
    process_ids: HashSet<u32>,
    windows: HashSet<isize>,
    unread_badges: HashSet<String>,
}

#[cfg(windows)]
fn title_indicates_unread_message(title: &str) -> bool {
    let normalized = title.trim().to_ascii_lowercase();
    if normalized.is_empty() {
        return false;
    }
    if ["新消息", "未读", "new message", "unread"]
        .iter()
        .any(|marker| normalized.contains(marker))
    {
        return true;
    }

    let starts_with_count = |open: char, close: char| {
        let Some(rest) = normalized.strip_prefix(open) else {
            return false;
        };
        let Some((count, _)) = rest.split_once(close) else {
            return false;
        };
        !count.is_empty() && count.chars().all(|character| character.is_ascii_digit())
    };
    starts_with_count('(', ')') || starts_with_count('[', ']')
}

#[cfg(windows)]
unsafe fn looks_like_message_popup(window: windows_sys::Win32::Foundation::HWND) -> bool {
    use windows_sys::Win32::{
        Foundation::RECT,
        Graphics::Gdi::{
            GetMonitorInfoW, MonitorFromWindow, MONITORINFO, MONITOR_DEFAULTTONEAREST,
        },
        UI::WindowsAndMessaging::{GetForegroundWindow, GetWindowRect, IsWindowVisible},
    };

    if window.is_null() || IsWindowVisible(window) == 0 || GetForegroundWindow() == window {
        return false;
    }
    let mut bounds = RECT::default();
    if GetWindowRect(window, &mut bounds) == 0 {
        return false;
    }
    let width = bounds.right - bounds.left;
    let height = bounds.bottom - bounds.top;
    if !(120..=760).contains(&width) || !(48..=520).contains(&height) {
        return false;
    }

    let monitor = MonitorFromWindow(window, MONITOR_DEFAULTTONEAREST);
    let mut monitor_info = MONITORINFO {
        cbSize: size_of::<MONITORINFO>() as u32,
        ..Default::default()
    };
    if monitor.is_null() || GetMonitorInfoW(monitor, &mut monitor_info) == 0 {
        return false;
    }
    let near_right_edge = bounds.right >= monitor_info.rcWork.right - 160;
    let near_bottom_edge = bounds.bottom >= monitor_info.rcWork.bottom - 160;
    let near_top_edge = bounds.top <= monitor_info.rcWork.top + 160;
    near_right_edge && (near_bottom_edge || near_top_edge)
}

#[cfg(windows)]
unsafe extern "system" fn collect_message_popup(
    window: windows_sys::Win32::Foundation::HWND,
    parameter: windows_sys::Win32::Foundation::LPARAM,
) -> windows_sys::core::BOOL {
    use windows_sys::Win32::UI::WindowsAndMessaging::{
        GetWindowTextLengthW, GetWindowTextW, GetWindowThreadProcessId, IsWindowVisible,
    };

    let scan = &mut *(parameter as *mut MessagePopupScan);
    let mut process_id = 0;
    GetWindowThreadProcessId(window, &mut process_id);
    if !scan.process_ids.contains(&process_id) {
        return 1;
    }

    if looks_like_message_popup(window) {
        scan.windows.insert(window as isize);
    }
    if IsWindowVisible(window) != 0 {
        let length = GetWindowTextLengthW(window);
        if length > 0 {
            let mut buffer = vec![0u16; length as usize + 1];
            let copied = GetWindowTextW(window, buffer.as_mut_ptr(), buffer.len() as i32);
            let title = String::from_utf16_lossy(&buffer[..copied.max(0) as usize]);
            if title_indicates_unread_message(&title) {
                scan.unread_badges
                    .insert(format!("{process_id}|{}", title.trim()));
            }
        }
    }
    1
}

#[cfg(windows)]
unsafe extern "system" fn message_window_event(
    _hook: windows_sys::Win32::UI::Accessibility::HWINEVENTHOOK,
    _event: u32,
    window: windows_sys::Win32::Foundation::HWND,
    object_id: i32,
    child_id: i32,
    _event_thread: u32,
    _event_time: u32,
) {
    use windows_sys::Win32::UI::WindowsAndMessaging::{GetWindowThreadProcessId, OBJID_WINDOW};

    if object_id != OBJID_WINDOW || child_id != 0 || window.is_null() {
        return;
    }
    let mut process_id = 0;
    GetWindowThreadProcessId(window, &mut process_id);
    let tracked = MESSAGE_PROCESS_IDS
        .get()
        .and_then(|ids| ids.lock().ok())
        .map(|ids| ids.contains(&process_id))
        .unwrap_or(false);
    if tracked && looks_like_message_popup(window) {
        MESSAGE_POPUP_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    }
}

#[cfg(windows)]
fn install_message_window_monitor() -> bool {
    use windows_sys::Win32::{
        UI::Accessibility::SetWinEventHook,
        UI::WindowsAndMessaging::{
            EVENT_OBJECT_SHOW, WINEVENT_OUTOFCONTEXT, WINEVENT_SKIPOWNPROCESS,
        },
    };

    let hook = unsafe {
        SetWinEventHook(
            EVENT_OBJECT_SHOW,
            EVENT_OBJECT_SHOW,
            null_mut(),
            Some(message_window_event),
            0,
            0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
        )
    };
    if hook.is_null() {
        return false;
    }
    MESSAGE_WINDOW_HOOK.store(hook as isize, Ordering::Relaxed);
    true
}

#[cfg(windows)]
fn is_legacy_message_process(name: &str) -> bool {
    let name = name.to_ascii_lowercase();
    LEGACY_MESSAGE_PROCESSES.contains(&name.as_str())
}

#[cfg(windows)]
fn inspect_new_message_popup(processes: &[(u32, String)]) -> bool {
    use windows_sys::Win32::UI::WindowsAndMessaging::EnumWindows;

    let process_ids: HashSet<u32> = processes
        .iter()
        .filter(|(_, name)| is_legacy_message_process(name))
        .map(|(process_id, _)| *process_id)
        .collect();
    if let Ok(mut tracked) = MESSAGE_PROCESS_IDS
        .get_or_init(|| Mutex::new(HashSet::new()))
        .lock()
    {
        *tracked = process_ids.clone();
    }
    let mut scan = MessagePopupScan {
        process_ids,
        windows: HashSet::new(),
        unread_badges: HashSet::new(),
    };
    if !scan.process_ids.is_empty() {
        unsafe {
            EnumWindows(
                Some(collect_message_popup),
                &mut scan as *mut MessagePopupScan as isize,
            );
        }
    }

    let tracker = KNOWN_MESSAGE_POPUPS.get_or_init(|| Mutex::new(None));
    let Ok(mut known) = tracker.lock() else {
        return false;
    };
    let polled_popup = known
        .as_ref()
        .map(|previous| scan.windows.iter().any(|window| !previous.contains(window)))
        .unwrap_or(false);
    *known = Some(scan.windows);
    let badge_tracker = KNOWN_MESSAGE_BADGES.get_or_init(|| Mutex::new(None));
    let new_unread_badge = badge_tracker
        .lock()
        .ok()
        .map(|mut known_badges| {
            let changed = known_badges.as_ref().is_some_and(|previous| {
                scan.unread_badges
                    .iter()
                    .any(|badge| !previous.contains(badge))
            });
            *known_badges = Some(scan.unread_badges);
            changed
        })
        .unwrap_or(false);
    let event_sequence = MESSAGE_POPUP_SEQUENCE.load(Ordering::Relaxed);
    let reported_sequence = REPORTED_MESSAGE_POPUP_SEQUENCE.swap(event_sequence, Ordering::Relaxed);
    polled_popup || new_unread_badge || event_sequence != reported_sequence
}

#[cfg(windows)]
fn running_processes() -> Vec<(u32, String)> {
    use windows_sys::Win32::{
        Foundation::{CloseHandle, INVALID_HANDLE_VALUE},
        System::Diagnostics::ToolHelp::{
            CreateToolhelp32Snapshot, Process32FirstW, Process32NextW, PROCESSENTRY32W,
            TH32CS_SNAPPROCESS,
        },
    };

    unsafe {
        let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if snapshot == INVALID_HANDLE_VALUE {
            return Vec::new();
        }

        let mut entry = PROCESSENTRY32W::default();
        entry.dwSize = size_of::<PROCESSENTRY32W>() as u32;
        let mut processes = Vec::new();
        if Process32FirstW(snapshot, &mut entry) != 0 {
            loop {
                let length = entry
                    .szExeFile
                    .iter()
                    .position(|character| *character == 0)
                    .unwrap_or(entry.szExeFile.len());
                processes.push((
                    entry.th32ProcessID,
                    String::from_utf16_lossy(&entry.szExeFile[..length]).to_ascii_lowercase(),
                ));
                if Process32NextW(snapshot, &mut entry) == 0 {
                    break;
                }
            }
        }
        CloseHandle(snapshot);
        processes
    }
}

#[cfg(windows)]
fn inspect_task_processes(processes: &[(u32, String)]) -> (bool, Option<bool>) {
    use windows_sys::Win32::{
        Foundation::CloseHandle,
        System::Threading::{GetExitCodeProcess, OpenProcess, PROCESS_QUERY_LIMITED_INFORMATION},
    };

    const SYNCHRONIZE_ACCESS: u32 = 0x0010_0000;
    const STILL_ACTIVE: u32 = 259;

    let current_tasks: HashSet<u32> = processes
        .iter()
        .filter(|(_, name)| TASK_PROCESSES.contains(&name.as_str()))
        .map(|(process_id, _)| *process_id)
        .collect();
    let tracker = TRACKED_TASKS.get_or_init(|| Mutex::new(HashMap::new()));
    let Ok(mut tracked) = tracker.lock() else {
        return (!current_tasks.is_empty(), None);
    };

    let finished_ids: Vec<u32> = tracked
        .keys()
        .filter(|process_id| !current_tasks.contains(process_id))
        .copied()
        .collect();
    let mut finished_task_succeeded = None;
    for process_id in finished_ids {
        if let Some(raw_handle) = tracked.get(&process_id).copied() {
            let handle = raw_handle as windows_sys::Win32::Foundation::HANDLE;
            let mut exit_code = STILL_ACTIVE;
            unsafe {
                let exit_code_ready =
                    GetExitCodeProcess(handle, &mut exit_code) != 0 && exit_code != STILL_ACTIVE;
                if exit_code_ready {
                    let succeeded = exit_code == 0;
                    if current_tasks.is_empty() {
                        finished_task_succeeded = Some(
                            finished_task_succeeded
                                .map(|previous| previous && succeeded)
                                .unwrap_or(succeeded),
                        );
                    }
                    tracked.remove(&process_id);
                    CloseHandle(handle);
                }
            }
        }
    }

    for process_id in &current_tasks {
        if tracked.contains_key(process_id) {
            continue;
        }
        let handle = unsafe {
            OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE_ACCESS,
                0,
                *process_id,
            )
        };
        if !handle.is_null() {
            tracked.insert(*process_id, handle as isize);
        }
    }

    (!current_tasks.is_empty(), finished_task_succeeded)
}

#[cfg(windows)]
#[tauri::command]
fn system_activity_snapshot() -> SystemActivitySnapshot {
    let processes = running_processes();
    let debugger_running = processes
        .iter()
        .any(|(_, name)| DEBUGGER_PROCESSES.contains(&name.as_str()));
    let (task_process_running, finished_task_succeeded) = inspect_task_processes(&processes);
    let (keyboard_idle_seconds, keyboard_sequence) = keyboard_activity();
    let (foreground_process, foreground_kind) = foreground_context();
    let (notification_access, notification_message_received) = inspect_new_message_notification();
    let popup_message_received = inspect_new_message_popup(&processes);
    if notification_message_received || popup_message_received {
        MESSAGE_SIGNAL_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    }
    SystemActivitySnapshot {
        idle_seconds: system_idle_seconds(),
        keyboard_idle_seconds,
        keyboard_sequence,
        foreground_process,
        foreground_kind,
        debugger_running,
        task_process_running,
        finished_task_succeeded,
        notification_access,
        message_signal_sequence: MESSAGE_SIGNAL_SEQUENCE.load(Ordering::Relaxed),
    }
}

#[cfg(not(windows))]
#[tauri::command]
fn system_activity_snapshot() -> SystemActivitySnapshot {
    SystemActivitySnapshot {
        idle_seconds: 0,
        keyboard_idle_seconds: None,
        keyboard_sequence: 0,
        foreground_process: String::new(),
        foreground_kind: "other".to_string(),
        debugger_running: false,
        task_process_running: false,
        finished_task_succeeded: None,
        notification_access: "unavailable".to_string(),
        message_signal_sequence: 0,
    }
}

#[cfg(not(windows))]
#[tauri::command]
fn foreground_process() -> String {
    String::new()
}

#[cfg(not(windows))]
#[tauri::command]
fn notification_access_status() -> String {
    "unavailable".to_string()
}

#[cfg(not(windows))]
#[tauri::command]
fn request_notification_access() -> Result<String, String> {
    Ok("unavailable".to_string())
}

#[cfg(all(test, windows))]
mod tests {
    use super::{
        auto_start_command, clamp_pet_scale, foreground_kind, is_legacy_message_process,
        is_message_notification_source, notification_identity, pet_window_dimensions,
        title_indicates_unread_message,
    };

    #[test]
    fn clamps_pet_scale_to_fifty_through_one_hundred_percent() {
        assert_eq!(clamp_pet_scale(0), 50);
        assert_eq!(clamp_pet_scale(40), 50);
        assert_eq!(clamp_pet_scale(50), 50);
        assert_eq!(clamp_pet_scale(85), 85);
        assert_eq!(clamp_pet_scale(100), 100);
        assert_eq!(clamp_pet_scale(115), 100);
    }

    #[test]
    fn reserves_menu_space_above_the_scaled_pet() {
        assert_eq!(pet_window_dimensions(50, false), (210.0, 205.0));
        assert_eq!(pet_window_dimensions(50, true), (224.0, 497.0));
        assert_eq!(pet_window_dimensions(100, true), (420.0, 702.0));
    }

    #[test]
    fn classifies_common_local_work_apps() {
        assert_eq!(
            foreground_kind(r"C:\Program Files\Codex\Codex.exe", "Codex"),
            "coding"
        );
        assert_eq!(
            foreground_kind(
                r"C:\Program Files\WindowsApps\OpenAI.Codex\ChatGPT.exe",
                "ChatGPT"
            ),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\__USER__\.local\bin\claude.exe", "Claude Code"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\__USER__\.local\bin\hermes.exe", "Hermes AI"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Qoder\Qoder.exe", "Qoder"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\__USER__\.opencode\bin\opencode.exe", "OpenCode"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\TRAE\TRAE.exe", "TRAE"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Windsurf\Windsurf.exe", "Windsurf"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Windows\System32\mspaint.exe", "无标题 - 画图"),
            "creative"
        );
        assert_eq!(
            foreground_kind(r"C:\Windows\System32\notepad.exe", "工作记录.txt"),
            "writing"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\WPS Office\wps.exe", "方案.docx"),
            "writing"
        );
        assert_eq!(
            foreground_kind(r"C:\Windows\explorer.exe", "项目计划.xlsx"),
            "writing"
        );
        assert_eq!(
            foreground_kind(r"C:\Windows\explorer.exe", "main.rs"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\WXWork\WXWork.exe", "企业微信"),
            "communication"
        );
        assert_eq!(
            foreground_kind(r"C:\__USER__\AppData\Local\Discord\Discord.exe", "Discord"),
            "communication"
        );
    }

    #[test]
    fn classifies_supported_browser_context_without_exposing_title() {
        assert_eq!(
            foreground_kind(r"C:\Program Files\Google\Chrome\chrome.exe", "Codex"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Google\Chrome\chrome.exe", "Claude Code"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Google\Chrome\chrome.exe", "OpenClaw"),
            "coding"
        );
        assert_eq!(
            foreground_kind(
                r"C:\Program Files\Google\Chrome\chrome.exe",
                "Hermes AI Agent"
            ),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Google\Chrome\chrome.exe", "Lovable"),
            "coding"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Google\Chrome\chrome.exe", "腾讯文档"),
            "writing"
        );
        assert_eq!(
            foreground_kind(r"C:\Program Files\Google\Chrome\chrome.exe", "普通网页"),
            "browser"
        );
    }

    #[test]
    fn accepts_message_apps_but_not_generic_notifications() {
        assert!(is_message_notification_source("Microsoft Teams"));
        assert!(is_message_notification_source("腾讯微信"));
        assert!(is_message_notification_source("Feishu 飞书"));
        assert!(is_message_notification_source("企业微信 WeCom"));
        assert!(is_message_notification_source("Telegram Desktop"));
        assert!(!is_message_notification_source("Windows 安全中心"));
        assert!(!is_message_notification_source("天气"));
    }

    #[test]
    fn distinguishes_reused_notification_ids_by_creation_time() {
        let first = notification_identity("Tencent Weixin", 1, 100);
        let replacement = notification_identity("Tencent Weixin", 1, 101);
        assert_ne!(first, replacement);
    }

    #[test]
    fn limits_legacy_popup_detection_to_known_message_processes() {
        assert!(is_legacy_message_process("Weixin.exe"));
        assert!(is_legacy_message_process("QQ.exe"));
        assert!(is_legacy_message_process("Telegram.exe"));
        assert!(is_legacy_message_process("WeChatAppEx.exe"));
        assert!(is_legacy_message_process("Outlook.exe"));
        assert!(is_legacy_message_process("WhatsApp.exe"));
        assert!(is_legacy_message_process("QQNT.exe"));
        assert!(is_legacy_message_process("Foxmail.exe"));
        assert!(!is_legacy_message_process("explorer.exe"));
    }

    #[test]
    fn recognizes_unread_window_title_markers() {
        assert!(title_indicates_unread_message("(3) 飞书"));
        assert!(title_indicates_unread_message("[12] QQ"));
        assert!(title_indicates_unread_message("2 条新消息 - 微信"));
        assert!(title_indicates_unread_message("Unread - Outlook"));
        assert!(!title_indicates_unread_message("飞书"));
        assert!(!title_indicates_unread_message("项目计划 (2026)"));
    }

    #[test]
    fn quotes_auto_start_executable_path() {
        assert_eq!(
            auto_start_command(std::path::Path::new(
                r"C:\Program Files\__PRODUCT_NAME__\__PRODUCT_NAME__.exe"
            )),
            r#""C:\Program Files\__PRODUCT_NAME__\__PRODUCT_NAME__.exe""#
        );
    }
}

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            #[cfg(windows)]
            let _keyboard_monitor_ready = install_keyboard_monitor();
            #[cfg(windows)]
            let _message_window_monitor_ready = install_message_window_monitor();
            #[cfg(windows)]
            let _auto_start_ready = initialize_auto_start();

            let window_config = app
                .config()
                .app
                .windows
                .iter()
                .find(|window| window.label == "main")
                .cloned()
                .ok_or_else(|| {
                    std::io::Error::new(
                        std::io::ErrorKind::NotFound,
                        "missing main window configuration",
                    )
                })?;
            let webview_data_dir = app
                .path()
                .app_local_data_dir()?
                .join(format!("webview-v{}", app.package_info().version));
            let window = WebviewWindowBuilder::from_config(app, &window_config)?
                .data_directory(webview_data_dir)
                .build()?;

            let show = MenuItem::with_id(app, "show", "显示桌宠", true, None::<&str>)?;
            let drink = MenuItem::with_id(app, "drink-water", "喝水提醒", true, None::<&str>)?;
            let rest = MenuItem::with_id(app, "resting", "开始休息", true, None::<&str>)?;
            let encouragement =
                MenuItem::with_id(app, "encouragement", "给我鼓励", true, None::<&str>)?;
            let random =
                MenuItem::with_id(app, "random-state", "随机更换状态", true, None::<&str>)?;
            let hide = MenuItem::with_id(app, "hide", "隐藏桌宠", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let menu = Menu::with_items(
                app,
                &[&show, &random, &drink, &rest, &encouragement, &hide, &quit],
            )?;

            TrayIconBuilder::with_id("main")
                .tooltip("__PRODUCT_NAME__")
                .icon(
                    app.default_window_icon()
                        .expect("missing application icon")
                        .clone(),
                )
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = position_bottom_right(&window);
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.hide();
                        }
                    }
                    "quit" => app.exit(0),
                    state => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.emit("tray-action", state);
                        }
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        if let Some(window) = tray.app_handle().get_webview_window("main") {
                            let _ = window.show();
                        }
                    }
                })
                .build(app)?;

            let _ = resize_pet_window(&window, read_saved_pet_scale(app.handle()), false);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            system_idle_seconds,
            foreground_process,
            system_activity_snapshot,
            notification_access_status,
            request_notification_access,
            get_pet_scale,
            set_pet_scale,
            set_context_menu_open,
            position_pet_bottom_right,
            quit_app,
            auto_start_enabled,
            set_auto_start
        ])
        .run(tauri::generate_context!())
        .expect("error while running desktop pet");
}
