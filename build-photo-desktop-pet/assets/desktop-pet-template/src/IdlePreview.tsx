import { invoke } from "@tauri-apps/api/core";
import { PhysicalPosition } from "@tauri-apps/api/dpi";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { Pause, Play, RotateCcw, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  CATEGORY_LABELS,
  isPetMotionId,
  MOTION_BY_ID,
  PET_MOTIONS,
  type PetMotionCategory,
  type PetMotionId,
} from "./petMotions";
import { createWorkSessionState, evaluateWorkActivity, type ForegroundKind } from "./workActivity";

const appWindow = window.__TAURI_INTERNALS__ ? getCurrentWindow() : null;
const FIFTEEN_MINUTES_MS = 15 * 60 * 1000;
const FIFTY_MINUTES_MS = 50 * 60 * 1000;
const SIXTY_MINUTES_MS = 60 * 60 * 1000;
const previewStretchDelay = Number(new URLSearchParams(window.location.search).get("stretchAfterMs"));
const AUTO_STRETCH_DELAY_MS = !appWindow && Number.isFinite(previewStretchDelay) && previewStretchDelay >= 500
  ? previewStretchDelay
  : FIFTEEN_MINUTES_MS;
const PREVIEW_SEQUENCE = PET_MOTIONS.map((motion) => motion.id);
const CATEGORY_ORDER: PetMotionCategory[] = ["default", "interaction", "work", "event", "reminder"];
const PET_SCALE_STORAGE_KEY = "__PRODUCT_SLUG__.pet-scale.v1";
const MESSAGE_NOTIFICATIONS_STORAGE_KEY = "__PRODUCT_SLUG__.message-notifications.v1";
const MIN_PET_SCALE = 50;
const MAX_PET_SCALE = 100;
const DEFAULT_PET_SCALE = 85;

function readSavedPetScale() {
  const saved = Number(window.localStorage.getItem(PET_SCALE_STORAGE_KEY));
  return Number.isFinite(saved) && saved >= MIN_PET_SCALE && saved <= MAX_PET_SCALE
    ? saved
    : DEFAULT_PET_SCALE;
}

function readSavedMessageNotifications() {
  return window.localStorage.getItem(MESSAGE_NOTIFICATIONS_STORAGE_KEY) !== "off";
}

type PreviewBackground = "checker" | "light" | "dark";

interface SystemActivitySnapshot {
  idleSeconds: number;
  keyboardIdleSeconds: number | null;
  keyboardSequence: number;
  foregroundProcess: string;
  foregroundKind: ForegroundKind;
  debuggerRunning: boolean;
  taskProcessRunning: boolean;
  finishedTaskSucceeded: boolean | null;
  notificationAccess: NotificationAccess;
  messageSignalSequence: number;
}

type NotificationAccess = "checking" | "allowed" | "denied" | "unspecified" | "unavailable";

interface PointerInteractionState {
  pointerId: number;
  startScreenX: number;
  startScreenY: number;
  latestScreenX: number;
  latestScreenY: number;
  dragging: boolean;
  windowX: number | null;
  windowY: number | null;
}

export default function IdlePreview() {
  const [motion, setMotion] = useState<PetMotionId>("idle");
  const [motionRun, setMotionRun] = useState(0);
  const [showBubble, setShowBubble] = useState(true);
  const [autoDemo, setAutoDemo] = useState(false);
  const [background, setBackground] = useState<PreviewBackground>("checker");
  const [petScale, setPetScale] = useState(readSavedPetScale);
  const [contextMenuOpen, setContextMenuOpen] = useState(false);
  const [notificationAccess, setNotificationAccess] = useState<NotificationAccess>("checking");
  const [messageNotificationsEnabled, setMessageNotificationsEnabled] = useState(readSavedMessageNotifications);
  const [autoStartEnabled, setAutoStartEnabled] = useState(true);
  const motionRef = useRef<PetMotionId>(motion);
  const baseMotionRef = useRef<PetMotionId>("idle");
  const temporaryUntilRef = useRef(0);
  const temporaryTimer = useRef<number | null>(null);
  const typingTimer = useRef<number | null>(null);
  const thinkingTimer = useRef<number | null>(null);
  const stretchTimer = useRef<number | null>(null);
  const pointerStart = useRef<PointerInteractionState | null>(null);
  const nativeWindowPosition = useRef<{ x: number; y: number } | null>(null);
  const nativeScaleFactor = useRef(window.devicePixelRatio || 1);
  const pendingWindowPosition = useRef<{ x: number; y: number } | null>(null);
  const windowMoveFrame = useRef<number | null>(null);
  const activeUsage = useRef({ lastSampleAt: Date.now(), breakMs: 0, waterMs: 0 });
  const workSession = useRef(createWorkSessionState());
  const lastMessageSignalSequence = useRef(0);

  const currentMotion = MOTION_BY_ID[motion];
  const usesSingleLineBubble = motion === "click" || motion === "drag";

  useEffect(() => {
    motionRef.current = motion;
    setShowBubble(true);
    const timer = window.setTimeout(() => setShowBubble(false), 4200);
    return () => window.clearTimeout(timer);
  }, [motion, motionRun]);

  const renderMotion = useCallback((next: PetMotionId) => {
    motionRef.current = next;
    setMotion(next);
    setMotionRun((run) => run + 1);
  }, []);

  const holdMotion = useCallback((next: PetMotionId) => {
    if (temporaryTimer.current !== null) window.clearTimeout(temporaryTimer.current);
    temporaryTimer.current = null;
    temporaryUntilRef.current = 0;
    baseMotionRef.current = next;
    renderMotion(next);
  }, [renderMotion]);

  const setContextMenuVisibility = useCallback(async (open: boolean) => {
    setContextMenuOpen(open);
    if (!appWindow) return nativeWindowPosition.current;
    try {
      const [x, y] = await invoke<[number, number]>("set_context_menu_open", { open });
      const position = { x, y };
      nativeWindowPosition.current = position;
      return position;
    } catch {
      return appWindow.outerPosition().catch(() => nativeWindowPosition.current);
    }
  }, []);

  const changePetScale = useCallback((nextScale: number) => {
    const safeScale = Math.min(MAX_PET_SCALE, Math.max(MIN_PET_SCALE, Math.round(nextScale / 5) * 5));
    setPetScale(safeScale);
    window.localStorage.setItem(PET_SCALE_STORAGE_KEY, String(safeScale));
    if (appWindow) void invoke<number>("set_pet_scale", { scale: safeScale, contextMenuOpen }).catch(() => undefined);
  }, [contextMenuOpen]);

  const setWorkMotion = useCallback((next: PetMotionId) => {
    baseMotionRef.current = next;
    if (Date.now() >= temporaryUntilRef.current && motionRef.current !== next) renderMotion(next);
  }, [renderMotion]);

  const playTemporary = useCallback((next: PetMotionId, durationMs = MOTION_BY_ID[next].previewDurationMs) => {
    const now = Date.now();
    const active = MOTION_BY_ID[motionRef.current];
    const incoming = MOTION_BY_ID[next];
    if (now < temporaryUntilRef.current && incoming.priority < active.priority) return false;

    if (temporaryTimer.current !== null) window.clearTimeout(temporaryTimer.current);
    temporaryUntilRef.current = now + durationMs;
    renderMotion(next);
    temporaryTimer.current = window.setTimeout(() => {
      temporaryUntilRef.current = 0;
      temporaryTimer.current = null;
      renderMotion(baseMotionRef.current);
    }, durationMs);
    return true;
  }, [renderMotion]);

  const beginDragCheer = useCallback(() => {
    if (temporaryTimer.current !== null) window.clearTimeout(temporaryTimer.current);
    temporaryTimer.current = null;
    temporaryUntilRef.current = Number.MAX_SAFE_INTEGER;
    if (motionRef.current !== "drag") renderMotion("drag");
  }, [renderMotion]);

  const finishDragCheer = useCallback(() => {
    if (motionRef.current !== "drag") return;
    temporaryUntilRef.current = Date.now() + MOTION_BY_ID.drag.previewDurationMs;
    temporaryTimer.current = window.setTimeout(() => {
      temporaryUntilRef.current = 0;
      temporaryTimer.current = null;
      renderMotion(baseMotionRef.current);
    }, MOTION_BY_ID.drag.previewDurationMs);
  }, [renderMotion]);

  const randomizeMotion = useCallback(() => {
    const candidates = PREVIEW_SEQUENCE.filter((item) => item !== "idle" && item !== motionRef.current);
    const next = candidates[Math.floor(Math.random() * candidates.length)] ?? "thinking";
    if (temporaryTimer.current !== null) window.clearTimeout(temporaryTimer.current);
    setAutoDemo(false);
    baseMotionRef.current = "idle";
    temporaryUntilRef.current = Date.now() + MOTION_BY_ID[next].previewDurationMs;
    renderMotion(next);
    temporaryTimer.current = window.setTimeout(() => {
      temporaryUntilRef.current = 0;
      temporaryTimer.current = null;
      baseMotionRef.current = "idle";
      renderMotion("idle");
    }, MOTION_BY_ID[next].previewDurationMs);
    setContextMenuVisibility(false);
  }, [renderMotion, setContextMenuVisibility]);

  const resetStretchTimer = useCallback(() => {
    if (stretchTimer.current !== null) window.clearTimeout(stretchTimer.current);
    stretchTimer.current = window.setTimeout(() => {
      playTemporary("stretch");
      resetStretchTimer();
    }, AUTO_STRETCH_DELAY_MS);
  }, [playTemporary]);

  const notePetInteraction = useCallback(() => {
    setAutoDemo(false);
    resetStretchTimer();
  }, [resetStretchTimer]);

  const startCoding = useCallback(() => {
    if (typingTimer.current !== null) window.clearTimeout(typingTimer.current);
    if (thinkingTimer.current !== null) window.clearTimeout(thinkingTimer.current);
    setWorkMotion("coding");
    typingTimer.current = window.setTimeout(() => {
      setWorkMotion("thinking");
      thinkingTimer.current = window.setTimeout(() => setWorkMotion("idle"), 6500);
    }, 2400);
  }, [setWorkMotion]);

  useEffect(() => {
    resetStretchTimer();
    return () => {
      if (temporaryTimer.current !== null) window.clearTimeout(temporaryTimer.current);
      if (typingTimer.current !== null) window.clearTimeout(typingTimer.current);
      if (thinkingTimer.current !== null) window.clearTimeout(thinkingTimer.current);
      if (stretchTimer.current !== null) window.clearTimeout(stretchTimer.current);
    };
  }, [resetStretchTimer]);

  useEffect(() => {
    if (!appWindow) return;
    void invoke<number>("get_pet_scale").then(setPetScale).catch(() => undefined);
    void invoke("position_pet_bottom_right").catch(() => undefined);
    void invoke<NotificationAccess>("notification_access_status").then(async (status) => {
      setNotificationAccess(status);
      if (status === "unspecified" && readSavedMessageNotifications()) {
        const requested = await invoke<NotificationAccess>("request_notification_access");
        setNotificationAccess(requested);
      }
    }).catch(() => setNotificationAccess("unavailable"));
    void invoke<boolean>("auto_start_enabled").then(setAutoStartEnabled).catch(() => {
      setAutoStartEnabled(false);
    });
  }, []);

  useEffect(() => {
    if (!appWindow) return;
    void Promise.all([appWindow.outerPosition(), appWindow.scaleFactor()]).then(([position, factor]) => {
      nativeWindowPosition.current = position;
      nativeScaleFactor.current = factor;
    }).catch(() => undefined);
    const unlistenMoved = appWindow.onMoved(({ payload: position }) => {
      nativeWindowPosition.current = position;
    });
    return () => {
      void unlistenMoved.then((unlisten) => unlisten());
      if (windowMoveFrame.current !== null) window.cancelAnimationFrame(windowMoveFrame.current);
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("button, input, textarea, select")) return;
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (event.key.length === 1 || ["Backspace", "Enter", "Tab"].includes(event.key)) startCoding();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [startCoding]);

  useEffect(() => {
    if (!appWindow) return;
    let cancelled = false;
    let checking = false;
    const detectWorkState = async () => {
      if (cancelled || checking) return;
      checking = true;
      try {
        const snapshot = await invoke<SystemActivitySnapshot>("system_activity_snapshot");
        if (cancelled) return;

        const now = Date.now();
        const elapsed = Math.min(3000, now - activeUsage.current.lastSampleAt);
        activeUsage.current.lastSampleAt = now;
        if (snapshot.idleSeconds < 60) {
          activeUsage.current.breakMs += elapsed;
          activeUsage.current.waterMs += elapsed;
        } else if (snapshot.idleSeconds >= 5 * 60) {
          activeUsage.current.breakMs = 0;
          activeUsage.current.waterMs = 0;
        }

        const workResult = evaluateWorkActivity(workSession.current, snapshot, now);
        setNotificationAccess(snapshot.notificationAccess);
        setWorkMotion(workResult.motion);
        if (!messageNotificationsEnabled) {
          lastMessageSignalSequence.current = snapshot.messageSignalSequence;
        } else if (snapshot.messageSignalSequence > lastMessageSignalSequence.current) {
          if (playTemporary("new-message")) {
            lastMessageSignalSequence.current = snapshot.messageSignalSequence;
          }
        } else if (snapshot.finishedTaskSucceeded === false) {
          playTemporary("error");
        } else if (snapshot.finishedTaskSucceeded === true || workResult.completedHumanWork) {
          playTemporary("task-complete");
        } else if (activeUsage.current.breakMs >= FIFTY_MINUTES_MS) {
          activeUsage.current.breakMs = 0;
          playTemporary("break-reminder");
        } else if (activeUsage.current.waterMs >= SIXTY_MINUTES_MS) {
          activeUsage.current.waterMs = 0;
          playTemporary("drink-water");
        }
      } catch {
        // Browser preview and unsupported systems use keyboard events and manual preview controls.
      } finally {
        checking = false;
      }
    };
    void detectWorkState();
    const timer = window.setInterval(() => void detectWorkState(), 1500);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [messageNotificationsEnabled, playTemporary, setWorkMotion]);

  useEffect(() => {
    if (!appWindow) return;
    const unlistenTray = listen<string>("tray-action", (event) => {
      if (event.payload === "random-state") {
        randomizeMotion();
        return;
      }
      const mapped: Partial<Record<string, PetMotionId>> = {
        "drink-water": "drink-water",
        resting: "idle",
        encouragement: "drag",
      };
      const next = mapped[event.payload];
      if (next === "idle") holdMotion(next);
      else if (next) playTemporary(next);
    });
    const unlistenMotion = listen<string>("pet-motion", (event) => {
      if (!isPetMotionId(event.payload)) return;
      if (["coding", "thinking", "processing", "debugging", "idle"].includes(event.payload)) {
        setWorkMotion(event.payload);
      } else {
        if (["task-complete", "error"].includes(event.payload) && ["processing", "debugging"].includes(baseMotionRef.current)) {
          baseMotionRef.current = "idle";
        }
        playTemporary(event.payload);
      }
    });
    return () => {
      void unlistenTray.then((unlisten) => unlisten());
      void unlistenMotion.then((unlisten) => unlisten());
    };
  }, [holdMotion, playTemporary, randomizeMotion, setWorkMotion]);

  useEffect(() => {
    if (!autoDemo) return;
    let index = PREVIEW_SEQUENCE.indexOf(motionRef.current);
    const advance = () => {
      index = (index + 1) % PREVIEW_SEQUENCE.length;
      holdMotion(PREVIEW_SEQUENCE[index]);
    };
    const timer = window.setInterval(advance, 3600);
    return () => window.clearInterval(timer);
  }, [autoDemo, holdMotion]);

  const groupedMotions = useMemo(() => CATEGORY_ORDER.map((category) => ({
    category,
    motions: PET_MOTIONS.filter((item) => item.category === category),
  })), []);

  const greet = () => {
    notePetInteraction();
    playTemporary("click");
  };

  const toggleMessageNotifications = useCallback(async () => {
    const enabled = !messageNotificationsEnabled;
    setMessageNotificationsEnabled(enabled);
    window.localStorage.setItem(MESSAGE_NOTIFICATIONS_STORAGE_KEY, enabled ? "on" : "off");
    if (!enabled || !appWindow || ["allowed", "unavailable", "checking"].includes(notificationAccess)) return;
    try {
      const status = await invoke<NotificationAccess>("request_notification_access");
      setNotificationAccess(status);
    } catch {
      setNotificationAccess("unavailable");
    }
  }, [messageNotificationsEnabled, notificationAccess]);

  const toggleAutoStart = useCallback(async () => {
    if (!appWindow) return;
    try {
      const enabled = await invoke<boolean>("set_auto_start", { enabled: !autoStartEnabled });
      setAutoStartEnabled(enabled);
    } catch {
      // Keep the displayed setting unchanged when Windows rejects the registry update.
    }
  }, [autoStartEnabled]);

  const schedulePointerWindowMove = (start: PointerInteractionState) => {
    if (!appWindow || !start.dragging || start.windowX === null || start.windowY === null) return;
    const deltaX = start.latestScreenX - start.startScreenX;
    const deltaY = start.latestScreenY - start.startScreenY;
    const factor = nativeScaleFactor.current;
    pendingWindowPosition.current = {
      x: Math.round(start.windowX + deltaX * factor),
      y: Math.round(start.windowY + deltaY * factor),
    };
    if (windowMoveFrame.current !== null) return;
    windowMoveFrame.current = window.requestAnimationFrame(() => {
      windowMoveFrame.current = null;
      const next = pendingWindowPosition.current;
      if (!next) return;
      nativeWindowPosition.current = next;
      void appWindow.setPosition(new PhysicalPosition(next.x, next.y)).catch((error) => {
        console.error("桌宠窗口移动失败", error);
      });
    });
  };

  const beginPointerInteraction = (event: React.PointerEvent<HTMLButtonElement>) => {
    if (event.button !== 0) return;
    notePetInteraction();
    const pointerId = event.pointerId;
    const menuWasOpen = contextMenuOpen;
    pointerStart.current = {
      pointerId,
      startScreenX: event.screenX,
      startScreenY: event.screenY,
      latestScreenX: event.screenX,
      latestScreenY: event.screenY,
      dragging: false,
      windowX: null,
      windowY: null,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
    void (async () => {
      const position = menuWasOpen
        ? await setContextMenuVisibility(false)
        : await appWindow?.outerPosition().catch(() => nativeWindowPosition.current);
      const start = pointerStart.current;
      if (!start || start.pointerId !== pointerId || !position) return;
      start.windowX = position.x;
      start.windowY = position.y;
      nativeWindowPosition.current = position;
      schedulePointerWindowMove(start);
    })();
  };

  const movePointerInteraction = (event: React.PointerEvent<HTMLButtonElement>) => {
    const start = pointerStart.current;
    if (!start) return;
    start.latestScreenX = event.screenX;
    start.latestScreenY = event.screenY;
    const deltaX = event.screenX - start.startScreenX;
    const deltaY = event.screenY - start.startScreenY;
    if (!start.dragging && Math.hypot(deltaX, deltaY) >= 7) {
      start.dragging = true;
      beginDragCheer();
    }
    schedulePointerWindowMove(start);
  };

  const endPointerInteraction = (event: React.PointerEvent<HTMLButtonElement>) => {
    const start = pointerStart.current;
    pointerStart.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    if (!start) return;
    if (start.dragging) finishDragCheer();
    else greet();
  };

  const selectPreviewMotion = (next: PetMotionId) => {
    setAutoDemo(false);
    holdMotion(next);
  };

  const openContextMenu = (event: React.MouseEvent<HTMLElement>) => {
    event.preventDefault();
    void setContextMenuVisibility(true);
  };

  const exitPet = () => {
    void setContextMenuVisibility(false);
    if (appWindow) void invoke("quit_app");
  };

  return (
    <div className="integrated-shell">
      <main
        className="integrated-pet-stage"
        style={{ "--pet-ui-scale": petScale / 100 } as CSSProperties}
        data-background={background}
        data-motion={motion}
        onContextMenu={openContextMenu}
        onPointerDown={(event) => {
          const target = event.target as HTMLElement;
          if (contextMenuOpen && !target.closest(".pet-context-menu, .integrated-pet-button")) {
            void setContextMenuVisibility(false);
          }
        }}
      >
        {showBubble && !contextMenuOpen && (
          <button
            className={usesSingleLineBubble ? "integrated-speech-bubble single-line" : "integrated-speech-bubble"}
            onClick={() => setShowBubble(false)}
          >
            {!usesSingleLineBubble && <strong>{currentMotion.label}</strong>}
            <span>{currentMotion.message}</span>
          </button>
        )}

        {contextMenuOpen && (
          <div
            className="pet-context-menu"
            role="menu"
            aria-label="桌宠快捷菜单"
            onPointerDown={(event) => event.stopPropagation()}
          >
            <button type="button" role="menuitem" onClick={randomizeMotion}>
              <span aria-hidden="true">🎲</span> 随机更换状态
            </button>
            <button
              type="button"
              role="menuitemcheckbox"
              aria-checked={messageNotificationsEnabled}
              onClick={toggleMessageNotifications}
            >
              <span aria-hidden="true">🔔</span>{" "}
              {messageNotificationsEnabled ? "消息提醒：已开启" : "消息提醒：已关闭"}
            </button>
            <button type="button" role="menuitemcheckbox" aria-checked={autoStartEnabled} onClick={toggleAutoStart}>
              <span aria-hidden="true">🚀</span>{" "}
              {autoStartEnabled ? "开机自动启动：已开启" : "开机自动启动：已关闭"}
            </button>
            <div className="pet-scale-control">
              <label htmlFor="pet-scale-range">
                <span>桌宠大小</span>
                <strong>{petScale}%</strong>
              </label>
              <div className="pet-scale-input-row">
                <button
                  type="button"
                  onClick={() => changePetScale(petScale - 5)}
                  disabled={petScale <= MIN_PET_SCALE}
                  aria-label="缩小桌宠"
                >−</button>
                <input
                  id="pet-scale-range"
                  type="range"
                  min={MIN_PET_SCALE}
                  max={MAX_PET_SCALE}
                  step="5"
                  value={petScale}
                  onChange={(event) => changePetScale(Number(event.currentTarget.value))}
                  aria-label="调整桌宠大小"
                />
                <button
                  type="button"
                  onClick={() => changePetScale(petScale + 5)}
                  disabled={petScale >= MAX_PET_SCALE}
                  aria-label="放大桌宠"
                >＋</button>
              </div>
              <div className="pet-scale-labels" aria-hidden="true"><span>小巧</span><span>标准</span><span>大号</span></div>
            </div>
            <button type="button" className="pet-menu-exit" role="menuitem" onClick={exitPet}>
              <span aria-hidden="true">⏻</span> 退出桌宠
            </button>
          </div>
        )}

        <button
          className="integrated-pet-button"
          onPointerDown={beginPointerInteraction}
          onPointerMove={movePointerInteraction}
          onPointerUp={endPointerInteraction}
          onPointerCancel={() => {
            if (pointerStart.current?.dragging) finishDragCheer();
            pointerStart.current = null;
          }}
          onContextMenu={(event) => {
            event.stopPropagation();
            openContextMenu(event);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              greet();
            }
          }}
          aria-label={`__PRODUCT_NAME__，当前状态：${currentMotion.label}。支持单击互动和拖动移动。`}
        >
          <img
            key={`${motion}-${motionRun}`}
            src={`${currentMotion.asset}?integrated=1`}
            alt={`${currentMotion.label}桌宠动效`}
            draggable={false}
          />
        </button>

      </main>

      {!appWindow && (
        <aside className="preview-control-panel" aria-label="全部桌宠动效预览控制台">
          <header className="preview-panel-header">
            <div>
              <span className="eyebrow">INTEGRATED PREVIEW · V1</span>
              <h1>__PRODUCT_NAME__全状态合成预览</h1>
              <p>13组已确认动效已接入同一画布、交互入口和优先级状态机。</p>
            </div>
            <div className="preview-summary"><strong>13</strong><span>组动效</span></div>
          </header>

          <section className="current-motion-card" aria-label="当前动效信息">
            <div className="current-motion-heading">
              <span className="current-motion-dot" />
              <strong>{currentMotion.label}</strong>
              <small>{currentMotion.assetVersion}</small>
            </div>
            <p>{currentMotion.trigger}</p>
            <div className="preview-actions">
              <button onClick={() => setMotionRun((run) => run + 1)}><RotateCcw size={15} />重新播放</button>
              <button onClick={startCoding}>模拟输入</button>
              <button className={autoDemo ? "active" : ""} onClick={() => setAutoDemo((value) => !value)}>
                {autoDemo ? <Pause size={15} /> : <Play size={15} />}{autoDemo ? "暂停巡检" : "自动巡检"}
              </button>
            </div>
          </section>

          <div className="background-switcher" aria-label="透明背景检查">
            <span>Alpha 背景</span>
            {(["checker", "light", "dark"] as PreviewBackground[]).map((item) => (
              <button key={item} className={background === item ? "active" : ""} onClick={() => setBackground(item)}>
                {item === "checker" ? "棋盘" : item === "light" ? "白色" : "深色"}
              </button>
            ))}
          </div>

          <div className="motion-groups">
            {groupedMotions.map(({ category, motions }) => (
              <section className="motion-group" key={category}>
                <h2>{CATEGORY_LABELS[category]}</h2>
                <div className="motion-grid">
                  {motions.map((item) => (
                    <button
                      key={item.id}
                      className={motion === item.id ? "motion-option active" : "motion-option"}
                      onClick={() => selectPreviewMotion(item.id)}
                      data-motion-id={item.id}
                    >
                      <span>{item.label}</span>
                      <small>{item.assetVersion}</small>
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </div>

          <footer className="preview-panel-footer">
            <Sparkles size={15} /> 单击桌宠测试招呼；按住桌宠移动测试拖动加油；“模拟输入”可测试编码与思考自动切换。
          </footer>
        </aside>
      )}
    </div>
  );
}
