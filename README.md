# Build Photo Desktop Pet Skill

[English](README_EN.md) | 简体中文

把一张人物或动物照片转换为可安装的 Q 版桌面宠物。角色会保留照片中的主要外观特征，并通过丰富的动作和表情陪伴用户工作、学习与休息。

## 功能

- 根据用户上传的单张照片设计专属 Q 版角色，保留人物或动物的发型、服装、配饰、花纹等辨识特征。
- 包含待机、点击问候、拖动加油、思考、敲代码、调试、任务完成、喝水和休息提醒等 13 种状态，让桌宠根据用户操作自然切换动作与表情。
- 支持点击互动和自由拖动；右键菜单显示在角色右上方且不会遮挡桌宠，大小可在 50%–100% 之间调整。
- 消息提醒可由用户随时开启或关闭，并会记住用户的选择。
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

Skill 会：

1. 根据照片制作 Q 版基础角色和程序图标。
2. 制作 13 种桌宠状态动画。
3. 集成点击、拖动、缩放、消息与工作场景互动。
4. 输出当前平台可安装的桌宠文件。

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

## 隐私说明

- 不读取键盘输入内容、剪贴板、聊天内容、文档内容或屏幕像素。
- 原始照片只用于当前项目，不会进入 Skill 包、模板或安装包。
- 不会把其他用户的角色、照片、路径或私有提示词作为示例或后备素材。

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

## 平台说明

- Windows 构建会输出当前用户安装的 NSIS 安装程序。
- macOS 版本必须在 Mac 上构建和验证。
- iPhone/iPad 不兼容桌面安装包；可复用动画资源，但需要单独开发并签名 iOS/iPadOS 应用。
- 未签名的 Windows 或 macOS 构建可能触发系统安全提醒。
