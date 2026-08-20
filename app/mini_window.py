"""前置小窗：始终置顶的小屏倒计时面板，可自由调整大小。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .task import TaskManager, format_ms


class MiniClockWindow(QWidget):
    """始终置顶的小窗，展示最近将结束的进行中任务倒计时。"""

    def __init__(
        self,
        manager: TaskManager,
        activate_main,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._manager = manager
        self._activate_main = activate_main

        self.setWindowTitle("计时小屏")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(150, 90)
        self.resize(230, 130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self._task_label = QLabel("暂无可显示任务")
        self._task_label.setAlignment(Qt.AlignCenter)
        self._task_label.setStyleSheet("QLabel { font-size: 12px; color: #666; }")
        layout.addWidget(self._task_label)

        self._time_label = QLabel("00:00")
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet(
            "QLabel { font-size: 34px; font-weight: bold; font-family: Consolas;"
            " color: #1f6feb; }"
        )
        layout.addWidget(self._time_label)

        buttons = QHBoxLayout()
        open_btn = QPushButton("打开主窗口")
        open_btn.clicked.connect(self._on_open_main)
        buttons.addWidget(open_btn)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.hide)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        # 数据联动
        manager.taskUpdated.connect(self._refresh)
        manager.timerFinished.connect(self._refresh)
        manager.taskAdded.connect(self._refresh)
        manager.taskRemoved.connect(self._refresh)
        self._refresh()

    # ---------- 事件 ----------
    def _active_task(self):
        """返回当前需要展示的倒计时任务。"""
        running = [t for t in self._manager.tasks if t.running]
        if not running:
            return None
        # 展示最近将结束（剩余最少）的那个
        return min(running, key=lambda t: t.remaining_ms)

    def _refresh(self, *_args) -> None:
        task = self._active_task()
        if task is None:
            self._task_label.setText("暂无进行中任务")
            self._time_label.setText("00:00")
            return
        self._task_label.setText(task.name)
        self._time_label.setText(format_ms(task.remaining_ms))

    def _on_open_main(self) -> None:
        self._activate_main()

    def closeEvent(self, event) -> None:
        # 关闭小窗只隐藏，不影响主窗口
        self.hide()
        event.ignore()