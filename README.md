# Build Photo Desktop Pet Skill

[English](README_EN.md) | 简体中文

把一张人物或动物照片转换为可安装的桌面宠物。该 Skill 面向 Codex，覆盖 Q 版角色设计、13 种状态动画、透明素材检查、Tauri 桌宠集成、原生运行验收和 Windows/macOS 安装包构建。

## 功能

- 从当前用户上传的单张照片提取角色特征，不复用其他用户的照片或角色素材。
- 生成符合比例门禁的 Q 版基础角色和六视图参考。
- 为 13 种桌宠状态分别生成并审核 12 帧透明动画。
- 检查残影、上下晃动、不规则缩放、裁切、肢体变形、碎片和阴影。
- 提供单击问候、拖动加油、工作状态、消息提醒、休息提醒等交互。
- 右键菜单不会遮挡角色，桌宠大小可在 50%–100% 之间调整。
- 使用 React、Vite 和 Tauri 生成轻量级桌宠应用。
- 支持 Windows x64 NSIS 安装包；macOS 构建需要在 macOS 上完成。
- 默认使用 Codex 内置 ImageGen；也保留了经用户明确授权后接入外部生图模型的适配接口。

## 13 种状态

`idle`、`click`、`drag`、`stretch`、`thinking`、`coding`、`processing`、`debugging`、`error`、`drink-water`、`task-complete`、`new-message`、`break-reminder`

## 安装

### 方法一：下载发布包

1. 在仓库的 **Releases** 页面下载最新 ZIP。
2. 解压后，将 `build-photo-desktop-pet` 文件夹复制到：

   - Windows：`%USERPROFILE%\.codex\skills\`
   - macOS/Linux：`~/.codex/skills/`

3. 重新打开 Codex 或新建一个任务。

### 方法二：克隆仓库

```powershell
git clone https://github.com/chx-123/build-photo-desktop-pet-skill.git
Copy-Item -Recurse -Force `
  .\build-photo-desktop-pet-skill\build-photo-desktop-pet `
  "$env:USERPROFILE\.codex\skills\build-photo-desktop-pet"
```

## 使用

在 Codex 中上传一张人物或动物照片，然后输入：

```text
$build-photo-desktop-pet 帮我把这张照片做成桌宠，并输出 Windows 安装文件
```

默认会：

1. 检查图片、ImageGen、Python、Node.js、Rust 和目标平台构建工具。
2. 生成并审核基础角色、转面参考和程序图标。
3. 分别制作 13 种状态动画。
4. 在原生 Tauri 窗口中测试交互、透明度、菜单位置和缩放。
5. 只有最终质量门禁通过后才输出安装包。

## 环境要求

- Codex，以及可用的内置 ImageGen。
- Python 3 和 Pillow。
- Node.js 与 npm。
- Rust 工具链。
- Windows 安装包：Windows x64 和对应的原生构建工具。
- macOS 安装包：macOS、Xcode Command Line Tools；正式分发还需要 Developer ID 签名与公证配置。

可先执行环境检查：

```powershell
python .\build-photo-desktop-pet\scripts\check_environment.py --json --target windows
```

## 外部生图模型

当 Codex 内置 ImageGen 不可用时，Skill 会停止生成并提示配置外部模型。只有用户明确同意把当前照片发送给指定服务后，才能使用：

```powershell
python .\build-photo-desktop-pet\scripts\external_image_provider.py --check
```

配置说明见：

`build-photo-desktop-pet/references/image-provider-configuration.md`

## 隐私与质量保证

- 不读取键盘输入内容、剪贴板、聊天内容、文档内容或屏幕像素。
- 原始照片只用于当前项目，不会进入 Skill 包、模板或安装包。
- 不会把其他用户的角色、照片、路径或私有提示词作为示例或后备素材。
- 每次发布都必须重新审核实际编码后的 13 个状态和原生运行效果。
- 质量门禁会阻止带有残影、晃动、异常缩放、裁切、动作断裂、变形碎片或人物/地面阴影的版本打包。

## 仓库结构

```text
.
├── README.md
├── README_EN.md
└── build-photo-desktop-pet/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

`README` 位于仓库根目录，不属于 Codex Skill 的运行上下文。实际安装时只需复制 `build-photo-desktop-pet` 文件夹。

## 验证

```powershell
python .\build-photo-desktop-pet\scripts\audit_skill_privacy.py `
  .\build-photo-desktop-pet

python .\build-photo-desktop-pet\scripts\test_skill_guards.py

$env:PYTHONUTF8 = "1"
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" `
  .\build-photo-desktop-pet
```

## 平台说明

- Windows 构建会输出当前用户安装的 NSIS 安装程序。
- macOS 版本必须在 Mac 上构建和验证。
- iPhone/iPad 不兼容桌面安装包；可复用动画资源，但需要单独开发并签名 iOS/iPadOS 应用。
- 未签名的 Windows 或 macOS 构建可能触发系统安全提醒。
