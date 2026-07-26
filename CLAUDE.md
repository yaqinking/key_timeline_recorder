# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

按键时间线记录器 - 一个使用 CustomTkinter 构建的桌面应用，用于记录、可视化和分析按键事件。支持全局按键监听、长按检测、APM 统计等功能。

## 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python key_timeline_recorder.py
```

**Windows 注意事项**: 可能需要以管理员身份运行才能正常监听全局按键。

## 核心架构

### KeyTimelineRecorder 类

主类负责整个应用逻辑，包含以下关键组件：

**状态管理**:
- `recording` - 记录状态标志
- `start_time` - 记录开始时间戳
- `key_events` - 按键事件列表
- `key_counts` - 按键计数字典
- `key_press_times` - 按键按下时间映射（用于计算持续时间和长按）

**两个键盘监听器**:
1. `hotkey_listener` - 始终运行，检测 `Ctrl+Alt+R` 快捷键来切换记录状态
2. `listener` - 仅在记录时运行，捕获所有按键事件（按下和释放）

### 按键事件数据结构

```python
{
    'key': 'A',                    # 按键原始名称
    'display_name': 'A (长按)',    # 显示名称（长按时添加标记）
    'timestamp': '14:32:15',       # 按下时间
    'elapsed': 3.5,                # 相对开始时间的偏移（秒）
    'duration': 0.5,               # 按键按住的时长（秒）
    'interval': 2.0,               # 与上一按键的间隔（秒）
    'count': 3,                    # 该按键的总次数
    'is_long_press': True          # 是否长按（>=0.5秒）
}
```

### 时间计算逻辑

1. **持续时间**: 按键释放时间 - 按键按下时间（从 `key_press_times` 字典获取）
2. **相对时间**: 按键释放时间 - 录制开始时间
3. **间隔时间**: 当前按键相对时间 - 上一按键相对时间

### UI 组件结构

```
主窗口 (1200x700)
├── 控制面板 (顶部，80px)
│   ├── 状态指示器 (彩色圆点)
│   ├── 状态标签
│   ├── 快捷键提示
│   └── 按钮（开始/停止、清除、导出）
├── 时间线区域 (中间)
│   └── Canvas 画布（可视化按键事件）
├── 详情表格 (中下)
│   └── Treeview 表格（7列：序号、按键、时间、相对时间、持续时间、间隔、次数）
└── 统计面板 (底部，80px)
    └── 4个统计卡片（总按键、APM、长按、时长）
```

## 关键常量

- `LONG_PRESS_THRESHOLD = 0.5` - 长按判定阈值（秒）

## 快捷键

- `Ctrl+Alt+R` - 开始/停止记录（全局有效）

## 依赖说明

| 库 | 用途 |
|---|---|
| `pynput` | 全局键盘监听 |
| `customtkinter` | 现代化 UI 组件 |
| `ttkbootstrap` | Treeview 表格样式 |

## 注意事项

- 记录时按键按下和释放都会被捕获，事件在**释放时**记录
- 长按标记在显示名称中添加 `(长按)`，在时间线中用黄色圆点 + 虚线圆环 + ⏱️ 图标标识
- 首个按键的间隔显示为 `-`
- APM 计算公式: `总按键数 / (总时长 / 60)`