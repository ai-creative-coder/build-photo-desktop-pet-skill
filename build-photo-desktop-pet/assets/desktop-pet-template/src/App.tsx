import { getCurrentWindow } from "@tauri-apps/api/window";
import { Check, ChevronLeft, Coffee, GripHorizontal, RotateCcw, Settings, X } from "lucide-react";
import { useEffect, useState } from "react";
import { PET_STATES, STATE_BY_ID, type PetStateId } from "./petStates";
import { usePetEngine, type PetSettings } from "./usePetEngine";

const appWindow = window.__TAURI_INTERNALS__ ? getCurrentWindow() : null;
const PET_ASSET_VERSION = "3";

function NumberSetting({ label, suffix, value, onChange }: { label: string; suffix: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="setting-row">
      <span>{label}</span>
      <span className="number-field">
        <input min="1" type="number" value={value} onChange={(event) => onChange(Math.max(1, Number(event.target.value)))} />
        <small>{suffix}</small>
      </span>
    </label>
  );
}

function SettingsPanel({ settings, onChange, onBack }: { settings: PetSettings; onChange: (settings: PetSettings) => void; onBack: () => void }) {
  const update = <K extends keyof PetSettings>(key: K, value: PetSettings[K]) => onChange({ ...settings, [key]: value });
  return (
    <section className="panel settings-panel" aria-label="桌宠设置">
      <header>
        <button className="icon-button" onClick={onBack} aria-label="返回状态列表"><ChevronLeft size={18} /></button>
        <strong>提醒与行为</strong>
        <span className="panel-spacer" />
      </header>
      <NumberSetting label="喝水提醒" suffix="分钟" value={settings.waterMinutes} onChange={(value) => update("waterMinutes", value)} />
      <NumberSetting label="休息提醒" suffix="分钟" value={settings.breakMinutes} onChange={(value) => update("breakMinutes", value)} />
      <NumberSetting label="伸展提醒" suffix="分钟" value={settings.stretchMinutes} onChange={(value) => update("stretchMinutes", value)} />
      <NumberSetting label="进入空闲" suffix="分钟" value={settings.idleMinutes} onChange={(value) => update("idleMinutes", value)} />
      <label className="setting-row">
        <span>下班时间</span>
        <input type="time" value={settings.offWorkTime} onChange={(event) => update("offWorkTime", event.target.value)} />
      </label>
      <label className="setting-row switch-row">
        <span>自动识别编码</span>
        <input type="checkbox" checked={settings.autoDetectCoding} onChange={(event) => update("autoDetectCoding", event.target.checked)} />
      </label>
      <label className="setting-row switch-row">
        <span>始终置顶</span>
        <input
          type="checkbox"
          checked={settings.alwaysOnTop}
          onChange={(event) => {
            update("alwaysOnTop", event.target.checked);
            void appWindow?.setAlwaysOnTop(event.target.checked).catch(() => undefined);
          }}
        />
      </label>
      <button className="reset-button" onClick={() => onChange({ waterMinutes: 45, breakMinutes: 50, stretchMinutes: 90, idleMinutes: 5, offWorkTime: "18:00", autoDetectCoding: true, alwaysOnTop: true })}>
        <RotateCcw size={15} /> 恢复默认设置
      </button>
    </section>
  );
}

function StatePanel({ current, onSelect, onSettings, onClose }: { current: PetStateId; onSelect: (state: PetStateId) => void; onSettings: () => void; onClose: () => void }) {
  return (
    <section className="panel state-panel" aria-label="切换桌宠状态">
      <header>
        <strong>现在要做什么？</strong>
        <div className="header-actions">
          <button className="icon-button" onClick={onSettings} aria-label="打开设置"><Settings size={17} /></button>
          <button className="icon-button" onClick={onClose} aria-label="关闭菜单"><X size={18} /></button>
        </div>
      </header>
      <div className="state-grid">
        {PET_STATES.map((item) => (
          <button key={item.id} className={current === item.id ? "state-option active" : "state-option"} onClick={() => onSelect(item.id)}>
            <img src={`/assets/pet/${item.id}.png?v=${PET_ASSET_VERSION}`} alt="" />
            <span>{item.label}</span>
            {current === item.id && <Check size={13} />}
          </button>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const { state, settings, setSettings, chooseManually } = usePetEngine();
  const [panel, setPanel] = useState<"states" | "settings" | null>(null);
  const [bubbleVisible, setBubbleVisible] = useState(true);
  const current = STATE_BY_ID[state];

  useEffect(() => {
    setBubbleVisible(true);
    const timer = window.setTimeout(() => setBubbleVisible(false), 6500);
    return () => window.clearTimeout(timer);
  }, [state]);

  const startDragging = (event: React.MouseEvent) => {
    if (event.button !== 0 || panel) return;
    void appWindow?.startDragging().catch(() => undefined);
  };

  return (
    <main className={`pet-stage state-${state}`} onContextMenu={(event) => { event.preventDefault(); setPanel("states"); }}>
      <button className="drag-handle" onMouseDown={startDragging} aria-label="拖动桌宠窗口">
        <GripHorizontal size={22} />
      </button>

      {bubbleVisible && !panel && (
        <button className="speech-bubble" onClick={() => setBubbleVisible(false)}>
          <strong>{current.label}</strong>
          <span>{current.message}</span>
        </button>
      )}

      <button
        className="pet-button"
        onMouseDown={startDragging}
        onClick={() => setPanel(panel ? null : "states")}
        onDoubleClick={() => chooseManually("encouragement")}
        aria-label={`${current.label}，单击打开菜单，双击获得鼓励`}
      >
        <img src={`/assets/pet/${state}.png?v=${PET_ASSET_VERSION}`} alt={`桌宠状态：${current.label}`} draggable={false} />
      </button>

      <div className="status-tag" aria-live="polite">
        <span className="status-dot" />{current.label}
      </div>

      {panel === "states" && <StatePanel current={state} onSelect={(next) => { chooseManually(next); setPanel(null); }} onSettings={() => setPanel("settings")} onClose={() => setPanel(null)} />}
      {panel === "settings" && <SettingsPanel settings={settings} onChange={setSettings} onBack={() => setPanel("states")} />}

      <div className="preview-hint">
        <Coffee size={16} /> 单击桌宠切换状态 · 双击桌宠获得鼓励 · 右键打开菜单
      </div>
    </main>
  );
}
