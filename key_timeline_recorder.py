"""
按键时间线记录器 - CustomTkinter 版本
按 Ctrl+Alt+R 开始/停止记录
"""

import time
from collections import defaultdict
from datetime import datetime
from pynput import keyboard
import customtkinter as ctk
import tkinter as tk
import json

# 设置主题
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class KeyTimelineRecorder:
    def __init__(self):
        self.recording = False
        self.start_time = None
        self.key_events = []
        self.key_counts = defaultdict(int)
        self.listener = None
        self.hotkey_listener = None

        # 长按检测
        self.key_press_times = {}  # 记录按键按下时间
        self.LONG_PRESS_THRESHOLD = 0.5  # 长按阈值（秒）

        # GUI setup
        self.root = ctk.CTk()
        self.root.title("⌨️ 按键时间线记录器")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)

        self.create_ui()
        self.setup_hotkey()

    def show_message(self, title, message):
        """显示消息对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")

        # 内容
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", 12),
            wraplength=340,
            justify="center"
        ).pack(expand=True)

        ctk.CTkButton(
            frame,
            text="确定",
            command=dialog.destroy,
            width=100,
            height=35
        ).pack(side=tk.BOTTOM, pady=(20, 0))

    def create_ui(self):
        """创建用户界面"""

        # 顶部控制面板
        control_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        control_frame.pack(fill=tk.X, side=tk.TOP)
        control_frame.pack_propagate(False)

        # 左侧状态
        self.status_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        self.status_frame.pack(side=tk.LEFT, padx=30, pady=20)

        # 状态指示器
        self.status_canvas = tk.Canvas(
            self.status_frame,
            width=16,
            height=16,
            bg="#1a1a2e",
            highlightthickness=0
        )
        self.status_canvas.pack(side=tk.LEFT, padx=(0, 12))
        self.update_status_indicator("#4ade80")  # 绿色

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="等待中 - 按 Ctrl+Alt+R 开始记录",
            font=("Segoe UI", 13),
            text_color="#4ade80"
        )
        self.status_label.pack(side=tk.LEFT)

        # 右侧按钮区
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(side=tk.RIGHT, padx=30, pady=15)

        # 快捷键提示
        hotkey_label = ctk.CTkLabel(
            button_frame,
            text="⌨️  Ctrl+Alt+R",
            font=("Segoe UI", 11),
            fg_color="#374151",
            corner_radius=8,
            padx=15,
            pady=8
        )
        hotkey_label.pack(side=tk.LEFT, padx=(0, 15))

        # 开始/停止按钮
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶ 开始记录",
            command=self.toggle_recording,
            font=("Segoe UI", 11, "bold"),
            width=130,
            height=40,
            fg_color="#3b82f6",
            hover_color="#60a5fa"
        )
        self.start_btn.pack(side=tk.LEFT, padx=8)

        # 清除按钮
        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️  清除",
            command=self.clear_data,
            font=("Segoe UI", 11),
            width=100,
            height=40,
            fg_color="#374151",
            hover_color="#4b5563"
        )
        self.clear_btn.pack(side=tk.LEFT, padx=8)

        # 导出按钮
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="📥 导出JSON",
            command=self.export_data,
            font=("Segoe UI", 11),
            width=120,
            height=40,
            fg_color="#374151",
            hover_color="#4b5563"
        )
        self.export_btn.pack(side=tk.LEFT, padx=8)

        # 主内容区域
        main_frame = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 时间线区域
        timeline_container = ctk.CTkFrame(main_frame, corner_radius=12)
        timeline_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(15, 10))

        # 时间线标题
        timeline_title = ctk.CTkLabel(
            timeline_container,
            text="📊 时间线",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        timeline_title.pack(fill=tk.X, padx=20, pady=(15, 10))

        # 画布区域
        canvas_frame = ctk.CTkFrame(timeline_container, fg_color="#111827", corner_radius=8)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.timeline_canvas = tk.Canvas(
            canvas_frame,
            bg="#111827",
            highlightthickness=0
        )
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 详情表格区域
        details_container = ctk.CTkFrame(main_frame, corner_radius=12)
        details_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 15))

        # 详情标题
        details_title = ctk.CTkLabel(
            details_container,
            text="📋 按键详情",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        details_title.pack(fill=tk.X, padx=20, pady=(15, 10))

        # 表格区域
        table_frame = ctk.CTkFrame(details_container, fg_color="#1f2937", corner_radius=8)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # 使用 ttk.Treeview
        import ttkbootstrap as ttk
        from ttkbootstrap import Style

        self.tree_style = Style(theme="superhero")
        self.tree = ttk.Treeview(
            table_frame,
            columns=("序号", "按键", "时间", "相对时间", "持续时间", "间隔", "次数"),
            show="headings",
            height=8,
            style="Treeview"
        )

        # 设置列
        columns_info = [
            ("序号", 50, "center"),
            ("按键", 100, "center"),
            ("时间", 150, "center"),
            ("相对时间", 90, "center"),
            ("持续时间", 75, "center"),
            ("间隔", 75, "center"),
            ("次数", 55, "center")
        ]

        for col_name, width, align in columns_info:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor=align, minwidth=50)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 统计面板
        self.create_stats_panel()

    def create_stats_panel(self):
        """创建统计面板"""
        stats_frame = ctk.CTkFrame(self.root, corner_radius=12, height=80)
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        stats_frame.pack_propagate(False)

        # 标题
        ctk.CTkLabel(
            stats_frame,
            text="📊 统计信息",
            font=("Segoe UI", 12, "bold"),
            fg_color="transparent"
        ).pack(side=tk.LEFT, padx=20, pady=15)

        # 统计项
        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        self.total_keys_label = self.create_stat_item("总按键", "0")
        self.apm_label = self.create_stat_item("APM", "0")
        self.long_press_label = self.create_stat_item("长按", "0")
        self.duration_label = self.create_stat_item("时长", "0s")

    def create_stat_item(self, title, initial_value):
        """创建单个统计项"""
        item_frame = ctk.CTkFrame(self.stats_container, fg_color="#1f2937", corner_radius=8, width=120)
        item_frame.pack(side=tk.LEFT, padx=8, expand=True, fill=tk.Y)
        item_frame.pack_propagate(False)

        value_label = ctk.CTkLabel(
            item_frame,
            text=initial_value,
            font=("Segoe UI", 20, "bold"),
            fg_color="transparent"
        )
        value_label.pack(side=tk.TOP, pady=(12, 2))

        title_label = ctk.CTkLabel(
            item_frame,
            text=title,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color="#9ca3af"
        )
        title_label.pack(side=tk.BOTTOM, pady=(0, 10))

        return value_label

    def update_status_indicator(self, color):
        """更新状态指示器颜色"""
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(
            3, 3, 13, 13,
            fill=color,
            outline=color
        )

    def setup_hotkey(self):
        """设置全局快捷键"""
        self.hotkey_pressed = set()

        def on_press(key):
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self.hotkey_pressed.add('ctrl')
                elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                    self.hotkey_pressed.add('alt')
                elif hasattr(key, 'char') and key.char and key.char.lower() == 'r':
                    self.hotkey_pressed.add('r')

                # 检查是否同时按下 Ctrl+Alt+R
                if ('ctrl' in self.hotkey_pressed and
                    'alt' in self.hotkey_pressed and
                    'r' in self.hotkey_pressed):
                    self.hotkey_pressed.clear()
                    self.root.after(100, self.toggle_recording)
            except Exception:
                pass

        def on_release(key):
            try:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self.hotkey_pressed.discard('ctrl')
                elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                    self.hotkey_pressed.discard('alt')
                elif hasattr(key, 'char') and key.char and key.char.lower() == 'r':
                    self.hotkey_pressed.discard('r')
            except Exception:
                pass

        self.hotkey_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.hotkey_listener.start()

    def on_key_press(self, key):
        """按键按下事件处理"""
        if not self.recording:
            return

        current_time = time.time()
        key_name = self.get_key_name(key)

        # 记录按键按下时间
        self.key_press_times[key_name] = current_time

    def on_key_release(self, key):
        """按键释放事件处理"""
        if not self.recording:
            return

        current_time = time.time()
        key_name = self.get_key_name(key)

        # 检查是否是之前按下的键
        if key_name in self.key_press_times:
            press_time = self.key_press_times[key_name]
            duration = current_time - press_time

            # 计算相对时间
            elapsed = current_time - self.start_time

            # 计算与上一个按键的间隔
            interval = 0
            if self.key_events:
                interval = elapsed - self.key_events[-1]['elapsed']

            self.key_counts[key_name] += 1

            # 判断是否长按
            is_long_press = duration >= self.LONG_PRESS_THRESHOLD
            display_name = f"{key_name} (长按)" if is_long_press else key_name

            event = {
                'key': key_name,
                'display_name': display_name,
                'timestamp': datetime.now().strftime('%H:%M:%S'),  # 移除毫秒
                'elapsed': elapsed,
                'duration': duration,
                'interval': interval,
                'count': self.key_counts[key_name],
                'is_long_press': is_long_press
            }
            self.key_events.append(event)

            # 移除按键记录
            del self.key_press_times[key_name]

            # 实时更新界面
            self.root.after(0, self.update_display)

    def get_key_name(self, key):
        """获取按键名称"""
        try:
            if hasattr(key, 'char') and key.char:
                if key.char == ' ':
                    return 'Space'
                return key.char.upper()
            elif hasattr(key, 'name'):
                return key.name.title()
            else:
                return str(key)
        except Exception:
            return 'Unknown'

    def toggle_recording(self):
        """切换记录状态"""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """开始记录"""
        if self.recording:
            return

        self.recording = True
        self.start_time = time.time()
        self.key_events = []
        self.key_counts.clear()
        self.key_press_times.clear()

        # 启动按键监听器（同时监听按下和释放）
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()

        self.update_status()
        self.show_message(
            title="开始记录",
            message="按键记录已开始！\n按 Ctrl+Alt+R 或点击停止按钮结束。\n\n💡 长按按键超过0.5秒会显示「长按」",
            icon="check"
        )

    def stop_recording(self):
        """停止记录"""
        if not self.recording:
            return

        self.recording = False

        if self.listener:
            self.listener.stop()
            self.listener = None

        self.key_press_times.clear()

        self.update_status()
        self.update_display()

        if self.key_events:
            # 统计长按次数
            long_press_count = sum(1 for e in self.key_events if e.get('is_long_press', False))
            message = f"记录已完成！\n共记录 {len(self.key_events)} 次按键事件\n耗时: {self.get_total_duration():.2f} 秒"
            if long_press_count > 0:
                message += f"\n\n⏱️ 长按: {long_press_count} 次"

            self.show_message(
                title="记录完成",
                message=message,
                icon="check"
            )

    def get_total_duration(self):
        """获取总时长"""
        if not self.key_events:
            return 0
        return self.key_events[-1]['elapsed']

    def update_status(self):
        """更新状态显示"""
        if self.recording:
            self.status_label.configure(
                text="记录中... - 按 Ctrl+Alt+R 停止",
                text_color="#f87171"  # 红色
            )
            self.start_btn.configure(
                text="■ 停止记录",
                fg_color="#ef4444",
                hover_color="#dc2626"
            )
            self.update_status_indicator("#ef4444")
        else:
            self.status_label.configure(
                text="等待中 - 按 Ctrl+Alt+R 开始记录",
                text_color="#4ade80"  # 绿色
            )
            self.start_btn.configure(
                text="▶ 开始记录",
                fg_color="#3b82f6",
                hover_color="#60a5fa"
            )
            self.update_status_indicator("#4ade80")

    def update_display(self):
        """更新显示"""
        self.draw_timeline()
        self.update_treeview()
        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        total_keys = len(self.key_events)
        duration = self.get_total_duration()
        long_press_count = sum(1 for e in self.key_events if e.get('is_long_press', False))

        # 计算 APM (Actions Per Minute)
        apm = 0
        if duration > 0:
            apm = round(total_keys / (duration / 60))

        # 格式化时长
        duration_str = self.format_duration(duration)

        # 更新标签
        self.total_keys_label.configure(text=str(total_keys))
        self.apm_label.configure(text=str(apm))
        self.long_press_label.configure(text=str(long_press_count))
        self.duration_label.configure(text=duration_str)

    def format_duration(self, seconds):
        """格式化时长显示"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def draw_timeline(self):
        """绘制时间线"""
        self.timeline_canvas.delete("all")

        if not self.key_events:
            self.timeline_canvas.create_text(
                400, 100,
                text="暂无记录数据\n点击「开始记录」或按 Ctrl+Alt+R",
                font=("Segoe UI", 14),
                fill="#9ca3af",
                justify=tk.CENTER
            )
            return

        # 时间线参数
        margin_left = 90
        margin_right = 30
        padding = 40
        height = self.timeline_canvas.winfo_height() or 250

        total_duration = self.get_total_duration()
        if total_duration == 0:
            total_duration = 1

        canvas_width = self.timeline_canvas.winfo_width() or 1200
        available_width = canvas_width - margin_left - margin_right

        # 绘制时间轴
        axis_y = height - 40
        self.timeline_canvas.create_line(
            margin_left, axis_y,
            margin_left + available_width, axis_y,
            width=2, fill="#374151"
        )

        # 时间刻度
        num_ticks = min(8, len(self.key_events))
        tick_interval = available_width / num_ticks

        self.timeline_canvas.create_text(
            margin_left, axis_y + 20,
            text="0s",
            font=("Segoe UI", 9),
            fill="#9ca3af"
        )

        for i in range(1, num_ticks + 1):
            x = margin_left + i * tick_interval
            time_label = f"{(total_duration * i / num_ticks):.1f}s"

            self.timeline_canvas.create_line(
                x, axis_y, x, axis_y + 5,
                width=2, fill="#3b82f6"
            )
            self.timeline_canvas.create_text(
                x, axis_y + 20,
                text=time_label,
                font=("Segoe UI", 9),
                fill="#9ca3af"
            )

        # 颜色
        color_palette = [
            "#f472b6", "#60a5fa", "#4ade80", "#fbbf24",
            "#a78bfa", "#2dd4bf", "#fb923c", "#f472b6",
            "#38bdf8", "#fb7185", "#818cf8", "#34d399"
        ]

        key_colors = {}
        unique_keys = sorted(set(e['key'] for e in self.key_events))
        for i, key in enumerate(unique_keys):
            key_colors[key] = color_palette[i % len(color_palette)]

        # 绘制按键事件
        row_height = 38
        used_rows = {}

        for event in self.key_events:
            x = margin_left + (event['elapsed'] / total_duration) * available_width

            key = event['key']
            if key not in used_rows:
                used_rows[key] = len(used_rows)

            row = used_rows[key]
            y = padding + row * row_height

            color = key_colors.get(key, "#3b82f6")

            # 按键标签
            if row == 0 or key != self.key_events[max(0, self.key_events.index(event) - 1)]['key']:
                self.timeline_canvas.create_rectangle(
                    8, y - 16, margin_left - 12, y + 16,
                    fill="#1f2937",
                    outline=color,
                    width=2
                )
                self.timeline_canvas.create_text(
                    (margin_left - 2) / 2, y,
                    text=key,
                    font=("Segoe UI", 10, "bold"),
                    fill=color
                )

            # 事件点
            is_long_press = event.get('is_long_press', False)
            radius = 7 + min(event['count'], 6)

            # 长按时使用不同的填充
            fill_color = color if not is_long_press else "#fbbf24"  # 长按用黄色
            outline_color = "#111827"

            self.timeline_canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill=fill_color, outline=outline_color, width=3
            )

            # 长按标记（圆环）
            if is_long_press:
                self.timeline_canvas.create_oval(
                    x - radius - 5, y - radius - 5,
                    x + radius + 5, y + radius + 5,
                    outline=fill_color, width=2, dash=(3, 3)
                )
                # 显示"长按"文字
                self.timeline_canvas.create_text(
                    x, y - radius - 20,
                    text="⏱️",
                    font=("Segoe UI", 12),
                    fill=fill_color
                )

            # 光晕效果
            if event['count'] >= 2:
                self.timeline_canvas.create_oval(
                    x - radius - 4, y - radius - 4,
                    x + radius + 4, y + radius + 4,
                    outline=color, width=1, dash=(2, 4)
                )

            # 次数标签
            if event['count'] > 1:
                label_y = y - radius - 20 if not is_long_press else y - radius - 32
                self.timeline_canvas.create_rectangle(
                    x - 14, label_y - 8,
                    x + 14, label_y + 8,
                    fill="#1f2937",
                    outline=color,
                    width=1
                )
                self.timeline_canvas.create_text(
                    x, label_y,
                    text=f"×{event['count']}",
                    font=("Segoe UI", 9, "bold"),
                    fill=color
                )

        # 连接线
        prev_events = {}
        for event in self.key_events:
            key = event['key']
            if key in prev_events:
                prev = prev_events[key]
                x1 = margin_left + (prev['elapsed'] / total_duration) * available_width
                row1 = used_rows[key]
                y1 = padding + row1 * row_height

                x2 = margin_left + (event['elapsed'] / total_duration) * available_width

                self.timeline_canvas.create_line(
                    x1, y1, x2, y1,
                    fill=key_colors.get(key, "#3b82f6"),
                    width=2, dash=(4, 4)
                )

            prev_events[key] = event

    def update_treeview(self):
        """更新详情表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, event in enumerate(self.key_events, 1):
            # 显示持续时间
            duration = event.get('duration', 0)
            duration_text = self.format_time_value(duration, is_duration=True)

            # 显示相对时间
            elapsed_text = self.format_time_value(event['elapsed'], is_duration=False)

            # 显示间隔时间
            interval = event.get('interval', 0)
            if idx == 1:
                interval_text = "-"
            else:
                interval_text = self.format_time_value(interval, is_duration=False)

            # 长按标识
            key_name = event.get('display_name', event['key'])

            self.tree.insert(
                "",
                tk.END,
                values=(
                    idx,
                    key_name,
                    event['timestamp'],
                    elapsed_text,
                    duration_text,
                    interval_text,
                    event['count']
                )
            )

    def format_time_value(self, seconds, is_duration=True):
        """格式化时间值"""
        if seconds < 0.001:
            return "<1ms"
        elif seconds < 0.01:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 0.1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 1:
            if is_duration:
                return f"{seconds:.3f}s"
            return f"{seconds:.2f}s"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def clear_data(self):
        """清除数据"""
        self.key_events = []
        self.key_counts.clear()
        self.update_display()
        self.timeline_canvas.delete("all")
        self.timeline_canvas.create_text(
            400, 100,
            text="数据已清除",
            font=("Segoe UI", 14),
            fill="#9ca3af"
        )

    def export_data(self):
        """导出数据为JSON"""
        if not self.key_events:
            self.show_message(title="导出失败", message="没有可导出的数据！", icon="cancel")
            return

        export_data = {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            'total_duration': self.get_total_duration(),
            'key_counts': dict(self.key_counts),
            'events': self.key_events
        }

        filename = f"key_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.show_message(
                title="导出成功",
                message=f"数据已导出到:\n{filename}",
                icon="check"
            )
        except Exception as e:
            self.show_message(
                title="导出失败",
                message=f"导出失败:\n{str(e)}",
                icon="cancel"
            )

    def run(self):
        """运行应用"""
        self.root.mainloop()

    def __del__(self):
        """清理资源"""
        if self.listener:
            self.listener.stop()
        if self.hotkey_listener:
            self.hotkey_listener.stop()


if __name__ == "__main__":
    try:
        app = KeyTimelineRecorder()
        app.run()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        self.show_message(
            title="错误",
            message=f"程序运行出错:\n{str(e)}",
            icon="cancel"
        )