import type { PetMotionId } from "./petMotions";

export type ForegroundKind = "coding" | "writing" | "communication" | "creative" | "browser" | "other";

export interface WorkActivitySnapshot {
  idleSeconds: number;
  keyboardIdleSeconds: number | null;
  keyboardSequence: number;
  foregroundKind: ForegroundKind;
  debuggerRunning: boolean;
  taskProcessRunning: boolean;
}

export interface WorkSessionState {
  startedAt: number | null;
  lastKeyboardSequence: number;
  lastMotion: PetMotionId;
}

export interface WorkActivityResult {
  motion: PetMotionId;
  completedHumanWork: boolean;
}

export const WORK_SESSION_IDLE_SECONDS = 10 * 60;
export const MIN_COMPLETABLE_SESSION_MS = 15_000;
const CODING_TO_THINKING_SECONDS = 30;

export function createWorkSessionState(): WorkSessionState {
  return {
    startedAt: null,
    lastKeyboardSequence: 0,
    lastMotion: "idle",
  };
}

function isFocusedWork(kind: ForegroundKind) {
  return kind === "coding" || kind === "writing" || kind === "communication" || kind === "creative";
}

function resetSession(state: WorkSessionState) {
  state.startedAt = null;
  state.lastMotion = "idle";
}

export function evaluateWorkActivity(
  state: WorkSessionState,
  snapshot: WorkActivitySnapshot,
  now: number,
): WorkActivityResult {
  if (snapshot.taskProcessRunning) {
    return { motion: "processing", completedHumanWork: false };
  }

  if (snapshot.debuggerRunning && (snapshot.foregroundKind === "coding" || state.startedAt !== null)) {
    state.lastMotion = "debugging";
    return { motion: "debugging", completedHumanWork: false };
  }

  const focusedWork = isFocusedWork(snapshot.foregroundKind);
  const receivedKeyboardInput = snapshot.keyboardSequence !== state.lastKeyboardSequence;
  state.lastKeyboardSequence = snapshot.keyboardSequence;
  if (focusedWork && receivedKeyboardInput) {
    if (state.startedAt === null) state.startedAt = now;
  }

  if (focusedWork && state.startedAt !== null && snapshot.idleSeconds < WORK_SESSION_IDLE_SECONDS) {
    const motion: PetMotionId = snapshot.foregroundKind === "coding"
      && snapshot.keyboardIdleSeconds !== null
      && snapshot.keyboardIdleSeconds <= CODING_TO_THINKING_SECONDS
      ? "coding"
      : "thinking";
    state.lastMotion = motion;
    return { motion, completedHumanWork: false };
  }

  if (state.startedAt === null) return { motion: "idle", completedHumanWork: false };

  const completedHumanWork = now - state.startedAt >= MIN_COMPLETABLE_SESSION_MS;
  resetSession(state);
  return { motion: "idle", completedHumanWork };
}
