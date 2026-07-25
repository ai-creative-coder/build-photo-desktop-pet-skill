export type PetMotionId =
  | "idle"
  | "click"
  | "drag"
  | "stretch"
  | "thinking"
  | "coding"
  | "processing"
  | "debugging"
  | "error"
  | "drink-water"
  | "task-complete"
  | "new-message"
  | "break-reminder";

export type PetMotionCategory = "default" | "interaction" | "work" | "event" | "reminder";

export interface PetMotionDefinition {
  id: PetMotionId;
  label: string;
  status: string;
  message: string;
  trigger: string;
  asset: string;
  assetVersion: string;
  category: PetMotionCategory;
  previewDurationMs: number;
  priority: number;
}

export const PET_MOTIONS: readonly PetMotionDefinition[] = [
  {
    id: "idle",
    label: "休息中",
    status: "默认状态 · 自然待机",
    message: "我在这里陪着你。",
    trigger: "没有更高优先级事件时循环播放",
    asset: "/assets/pet/integrated-v1/idle.png",
    assetVersion: "用户生成资产",
    category: "default",
    previewDurationMs: 4200,
    priority: 10,
  },
  {
    id: "click",
    label: "点击打招呼",
    status: "用户互动 · 友好招呼",
    message: "你好，很高兴见到你。",
    trigger: "单击桌宠后立即播放一轮",
    asset: "/assets/pet/integrated-v1/click.png",
    assetVersion: "用户生成资产",
    category: "interaction",
    previewDurationMs: 1680,
    priority: 125,
  },
  {
    id: "drag",
    label: "拖动加油",
    status: "用户互动 · 加油动作",
    message: "今天也要加油呀！",
    trigger: "按住桌宠并真实移动至少7像素，立即播放鼓励动作；松手后自然完成当前一轮",
    asset: "/assets/pet/integrated-v1/drag.png",
    assetVersion: "用户生成资产",
    category: "interaction",
    previewDurationMs: 1680,
    priority: 130,
  },
  {
    id: "stretch",
    label: "伸展活动",
    status: "定时提醒 · 舒展身体",
    message: "活动一下身体吧。",
    trigger: "桌宠连续打开且15分钟未点击或拖动",
    asset: "/assets/pet/integrated-v1/stretch.png",
    assetVersion: "用户生成资产",
    category: "reminder",
    previewDurationMs: 2160,
    priority: 80,
  },
  {
    id: "thinking",
    label: "思考中",
    status: "工作状态 · 思考反馈",
    message: "正在整理思路。",
    trigger: "支持的工作软件中出现持续输入或短暂停顿",
    asset: "/assets/pet/integrated-v1/thinking.png",
    assetVersion: "用户生成资产",
    category: "work",
    previewDurationMs: 4320,
    priority: 50,
  },
  {
    id: "coding",
    label: "编码中",
    status: "工作状态 · 输入动作与屏幕反馈",
    message: "正在处理代码。",
    trigger: "支持的代码编辑器、终端或编程工具中持续输入",
    asset: "/assets/pet/integrated-v1/coding.png",
    assetVersion: "用户生成资产",
    category: "work",
    previewDurationMs: 4200,
    priority: 65,
  },
  {
    id: "processing",
    label: "处理中",
    status: "任务状态 · 处理反馈",
    message: "任务正在处理。",
    trigger: "构建、导出、压缩或安装任务运行中",
    asset: "/assets/pet/integrated-v1/processing.png",
    assetVersion: "用户生成资产",
    category: "work",
    previewDurationMs: 4200,
    priority: 60,
  },
  {
    id: "debugging",
    label: "调试中",
    status: "工作状态 · 调试反馈",
    message: "正在检查问题。",
    trigger: "IDE调试会话或支持的调试器运行中",
    asset: "/assets/pet/integrated-v1/debugging.png",
    assetVersion: "用户生成资产",
    category: "work",
    previewDurationMs: 4480,
    priority: 70,
  },
  {
    id: "error",
    label: "发生错误",
    status: "异常事件 · 错误反馈",
    message: "检测到任务失败。",
    trigger: "构建、测试、脚本或导出任务失败",
    asset: "/assets/pet/integrated-v1/error.png",
    assetVersion: "用户生成资产",
    category: "event",
    previewDurationMs: 3840,
    priority: 110,
  },
  {
    id: "drink-water",
    label: "喝水提醒",
    status: "健康提醒 · 喝水互动",
    message: "记得补充水分。",
    trigger: "累计活跃用机60分钟后提醒",
    asset: "/assets/pet/integrated-v1/drink-water.png",
    assetVersion: "用户生成资产",
    category: "reminder",
    previewDurationMs: 4200,
    priority: 85,
  },
  {
    id: "task-complete",
    label: "任务完成",
    status: "成功事件 · 完成反馈",
    message: "任务已经完成。",
    trigger: "构建、测试、导出或下载任务成功结束",
    asset: "/assets/pet/integrated-v1/task-complete.png",
    assetVersion: "用户生成资产",
    category: "event",
    previewDurationMs: 3600,
    priority: 100,
  },
  {
    id: "new-message",
    label: "新消息提醒",
    status: "通知事件 · 新消息反馈",
    message: "收到一条新消息。",
    trigger: "Windows收到白名单新通知，或通讯软件出现新弹窗/未读标记",
    asset: "/assets/pet/integrated-v1/new-message.png",
    assetVersion: "用户生成资产",
    category: "event",
    previewDurationMs: 3480,
    priority: 150,
  },
  {
    id: "break-reminder",
    label: "休息提醒",
    status: "健康提醒 · 休息反馈",
    message: "请适当休息。",
    trigger: "连续活跃用机50分钟且最近没有充分离席",
    asset: "/assets/pet/integrated-v1/break-reminder.png",
    assetVersion: "用户生成资产",
    category: "reminder",
    previewDurationMs: 4320,
    priority: 85,
  },
];

export const MOTION_BY_ID = Object.fromEntries(PET_MOTIONS.map((motion) => [motion.id, motion])) as Record<
  PetMotionId,
  PetMotionDefinition
>;

export const CATEGORY_LABELS: Record<PetMotionCategory, string> = {
  default: "默认状态",
  interaction: "用户互动",
  work: "电脑工作",
  event: "任务与通知",
  reminder: "健康提醒",
};

export const isPetMotionId = (value: string): value is PetMotionId => value in MOTION_BY_ID;
