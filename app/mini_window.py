"""前置小窗：模拟微软时钟的"紧凑模式"。

主窗口和小窗是互斥显示的两种形态：切到小窗时隐藏主窗口、显示始终置顶的小窗；
小窗内含"回到主窗口"按钮，一键切回。小窗直接展示任务清单内容（含增删、计时控制）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .task import TaskManager
from .tasks_page import TasksPage


class MiniClockWindow(QWidget):
    """始终置顶、可缩放的小窗，展示任务清单全内容。"""

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
        # Qt.Tool：任务栏不出现独立条目；WindowStaysOnTopHint：始终置顶
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.resize(340, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("小窗模式")
        title.setStyleSheet("QLabel { font-weight: bold; font-size: 13px; }")
        header.addWidget(title)
        header.addStretch(1)
        expand_btn = QPushButton("⌂ 回到主窗口")
        expand_btn.clicked.connect(self._expand)
        header.addWidget(expand_btn)
        layout.addLayout(header)

        # 直接复用任务清单页，展示全部任务内容与计时控制
        self._tasks_page = TasksPage(manager, self)
        layout.addWidget(self._tasks_page, 1)

    def _expand(self) -> None:
        self._on_expand()

    def closeEvent(self, event) -> None:
        # 关闭小窗即回到主窗口，而不是退出
        self._on_expand()
        event.ignore()