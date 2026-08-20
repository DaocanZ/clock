"""前置小窗：聚焦倒计时的大字显示，下方一行当前任务提醒。

主窗口与小窗互斥切换（微软时钟紧凑模式）：切到小窗时隐藏主窗口、显示始终置顶的小窗；
小窗内含"回到主窗口"按钮。小窗可自由缩放到很小，不承载完整任务清单。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .task import TaskManager, format_ms


class MiniClockWindow(QWidget):
    def __init__(
        self,
        manager: TaskManager,
        on_expand: callable,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._manager = manager
        self._on_expand = on_expand

        self.setWindowTitle("我的时钟 · 小窗")
        # 始终置顶；Qt.Tool 使任务栏不出现独立条目
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 允许自由缩小到很小
        self.setMinimumSize(0, 0)
        self.resize(260, 170)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 6)
        layout.setSpacing(2)
        # 不依赖内容推导最小尺寸，实现任意缩放
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        header = QHBoxLayout()
        title = QLabel("小窗")
        title.setStyleSheet("QLabel { font-size: 11px; color: #888; }")
        header.addWidget(title)
        header.addStretch(1)
        expand_btn = QPushButton("⌂ 回到主窗口")
        expand_btn.clicked.connect(self._expand)
        header.addWidget(expand_btn)
        layout.addLayout(header)

        # 大字倒计时（字体随窗口尺寸动态缩放）
        self._time_label = QLabel("00:00")
        self._time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._time_label)

        # 下方一行：当前在做的任务提醒
        self._task_label = QLabel("暂无进行中任务")
        self._task_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._task_label)

        # 数据联动
        manager.taskUpdated.connect(self._refresh)
        manager.timerFinished.connect(self._refresh)
        manager.taskAdded.connect(self._refresh)
        manager.taskRemoved.connect(self._refresh)
        self._apply_scaled_font()
        self._refresh()

    # ---------- 事件 ----------
    def _active_task(self):
        """返回当前要提醒的任务：进行中任务里剩余时间最少的一个。"""
        running = [t for t in self._manager.tasks if t.running]
        if not running:
            return None
        return min(running, key=lambda t: t.remaining_ms)

    def _refresh(self, *_args) -> None:
        task = self._active_task()
        if task is None:
            self._task_label.setText("暂无进行中任务")
            self._time_label.setText("00:00")
            return
        self._task_label.setText(task.name)
        self._time_label.setText(format_ms(task.remaining_ms))

    def _apply_scaled_font(self) -> None:
        """随窗口大小调整字体：计时为主（约半窗高），任务一行为辅。"""
        h = self.height()
        time_size = max(13, min(110, int(h * 0.48)))
        self._time_label.setStyleSheet(
            f"QLabel {{ font-size: {time_size}px; font-weight: bold;"
            " font-family: Consolas; color: #1f6feb; }"
        )
        task_size = max(10, min(16, int(h * 0.09)))
        self._task_label.setStyleSheet(
            f"QLabel {{ font-size: {task_size}px; color: #444; }}"
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_scaled_font()

    def _expand(self) -> None:
        self._on_expand()

    def closeEvent(self, event) -> None:
        # 关闭小窗即回到主窗口，而不是退出
        self._on_expand()
        event.ignore()