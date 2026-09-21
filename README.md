# 会议纪要（meeting-minutes）

一个 Codex 技能：把会议录音、视频或已有的转写文本，整理成三份可交付物——图文纪要、带时间点的文字稿、待确认问题清单。

核心原则是忠实：只写录音里真实出现的内容，听不清的地方标 `[?]` 或 `[听不清]`，不猜测、不补全。

## 安装

克隆到 Codex 的技能目录。

Windows（PowerShell）：

```powershell
git clone https://github.com/chengwu0619/guo.git "$env:USERPROFILE\.codex\skills\meeting-minutes"
```

macOS / Linux：

```bash
git clone https://github.com/chengwu0619/guo.git ~/.codex/skills/meeting-minutes
```

## 使用

在 Codex 里直接说：

> 用 $meeting-minutes 把这段会议录音整理成图文纪要、带时间点的文字稿和待确认问题清单。

技能默认跟随录音语言输出，也可以先指定输出语言、交付格式（Word / Markdown）以及是否需要区分发言人。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `SKILL.md` | 技能主文件：流程、纪要结构、交付前复核清单 |
| `agents/openai.yaml` | 界面显示名与默认提示 |
| `references/transcription.md` | 转写环境、模型选择、长音频处理、说话人区分、故障排查 |
| `references/deliverables.md` | 三份交付物的模板与图示规范 |
| `scripts/transcribe.py` | 用 faster-whisper 转写，输出带时间点 JSON 与纯文本 |
| `scripts/download_model.py` | 并行、可断点续传地下载模型，并校验 sha256 |

## 依赖

- Python 3.9+
- `faster-whisper`（自带 PyAV 解码，不需要系统 ffmpeg）
- 本地转写模型，例如 `Systran/faster-whisper-large-v3`（约 3 GB），用 `scripts/download_model.py` 下载并校验
