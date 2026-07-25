export const PET_STATES = [
  { id: "thinking", label: "思考中", message: "慢慢来，我陪你一起想。" },
  { id: "coding", label: "编码中", message: "专注编码中，灵感正在加载。" },
  { id: "debugging", label: "调试中", message: "别急，我们把问题找出来。" },
  { id: "processing", label: "处理中", message: "任务处理中，请稍等一下。" },
  { id: "task-complete", label: "任务完成", message: "完成啦，做得真棒！" },
  { id: "error", label: "出错了", message: "遇到一点问题，检查一下吧。" },
  { id: "new-message", label: "新消息", message: "叮！你有一条新消息。" },
  { id: "drink-water", label: "喝水提醒", message: "工作辛苦啦，喝口水吧。" },
  { id: "break-reminder", label: "休息提醒", message: "已经工作一阵子，休息一下吧。" },
  { id: "resting", label: "休息中", message: "暂时放空一下，待会儿见。" },
  { id: "stretch", label: "伸展一下", message: "活动一下肩颈和手腕吧。" },
  { id: "encouragement", label: "加油鼓励", message: "保持节奏，你已经做得很好啦！" },
  { id: "idle", label: "空闲中", message: "我在这里等你回来。" },
  { id: "off-work", label: "下班啦", message: "今天辛苦了，明天见！" },
] as const;

export type PetStateId = (typeof PET_STATES)[number]["id"];

export const STATE_BY_ID = Object.fromEntries(PET_STATES.map((state) => [state.id, state])) as Record<
  PetStateId,
  (typeof PET_STATES)[number]
>;

export const STATE_PRIORITY: Record<PetStateId, number> = {
  error: 100,
  "new-message": 95,
  "task-complete": 90,
  "drink-water": 80,
  "break-reminder": 80,
  stretch: 80,
  debugging: 70,
  processing: 65,
  coding: 60,
  encouragement: 55,
  thinking: 40,
  resting: 35,
  idle: 30,
  "off-work": 20,
};

export const isTemporaryState = (state: PetStateId) => STATE_PRIORITY[state] >= 55 && state !== "coding";
