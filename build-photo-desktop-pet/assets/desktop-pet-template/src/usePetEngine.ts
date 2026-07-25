import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useCallback, useEffect, useRef, useState } from "react";
import type { PetStateId } from "./petStates";
import { isTemporaryState, STATE_PRIORITY } from "./petStates";

export interface PetSettings {
  waterMinutes: number;
  breakMinutes: number;
  stretchMinutes: number;
  idleMinutes: number;
  offWorkTime: string;
  autoDetectCoding: boolean;
  alwaysOnTop: boolean;
}

const DEFAULT_SETTINGS: PetSettings = {
  waterMinutes: 45,
  breakMinutes: 50,
  stretchMinutes: 90,
  idleMinutes: 5,
  offWorkTime: "18:00",
  autoDetectCoding: true,
  alwaysOnTop: true,
};

const EDITORS = ["code.exe", "cursor.exe", "idea64.exe", "webstorm64.exe", "pycharm64.exe", "devenv.exe", "sublime_text.exe", "notepad++.exe"];

function loadSettings(): PetSettings {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem("pet-settings") ?? "{}") };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function usePetEngine() {
  const [state, setState] = useState<PetStateId>("thinking");
  const [settings, setSettingsValue] = useState(loadSettings);
  const stateRef = useRef(state);
  const overrideUntil = useRef(0);
  const workStartedAt = useRef(Date.now());
  const lastWaterAt = useRef(Date.now());
  const lastStretchAt = useRef(Date.now());

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const setSettings = useCallback((next: PetSettings) => {
    setSettingsValue(next);
    localStorage.setItem("pet-settings", JSON.stringify(next));
  }, []);

  const showState = useCallback((next: PetStateId, durationMs = 9000) => {
    if (Date.now() < overrideUntil.current && STATE_PRIORITY[next] < STATE_PRIORITY[stateRef.current]) return;
    setState(next);
    stateRef.current = next;
    if (isTemporaryState(next)) overrideUntil.current = Date.now() + durationMs;
  }, []);

  const chooseManually = useCallback((next: PetStateId) => {
    setState(next);
    stateRef.current = next;
    overrideUntil.current = Date.now() + 60_000;
  }, []);

  useEffect(() => {
    if (!window.__TAURI_INTERNALS__) return;
    const unlisten = listen<string>("tray-action", (event) => chooseManually(event.payload as PetStateId));
    return () => {
      void unlisten.then((fn) => fn());
    };
  }, [chooseManually]);

  useEffect(() => {
    const poll = async () => {
      const now = Date.now();
      if (now < overrideUntil.current) return;

      const currentTime = new Date().toTimeString().slice(0, 5);
      if (currentTime >= settings.offWorkTime) {
        setState("off-work");
        return;
      }

      if (now - lastWaterAt.current >= settings.waterMinutes * 60_000) {
        lastWaterAt.current = now;
        showState("drink-water", 12_000);
        return;
      }
      if (now - workStartedAt.current >= settings.breakMinutes * 60_000) {
        workStartedAt.current = now;
        showState("break-reminder", 12_000);
        return;
      }
      if (now - lastStretchAt.current >= settings.stretchMinutes * 60_000) {
        lastStretchAt.current = now;
        showState("stretch", 12_000);
        return;
      }

      if (window.__TAURI_INTERNALS__) {
        try {
          const idleSeconds = await invoke<number>("system_idle_seconds");
          if (idleSeconds >= settings.idleMinutes * 60) {
            setState("idle");
            return;
          }
          if (settings.autoDetectCoding) {
            const process = (await invoke<string>("foreground_process")).toLowerCase();
            if (EDITORS.some((editor) => process.endsWith(editor))) {
              setState("coding");
              return;
            }
          }
        } catch {
          // Browser preview and unsupported systems use the neutral state.
        }
      }

      setState("thinking");
    };

    void poll();
    const timer = window.setInterval(poll, 5000);
    return () => window.clearInterval(timer);
  }, [settings, showState]);

  return { state, settings, setSettings, chooseManually, showState };
}
