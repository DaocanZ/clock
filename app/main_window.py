"""主窗口：聚合任务清单页与计时页。"""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from .alert import TimerAlertDialog
from .task import Task, TaskManager
from .tasks_page import TasksPage
from .timer_page import TimerPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("我的时钟")
        self.resize(760, 560)

        self._manager = TaskManager(self)
        # 任何任务倒计时结束都弹出闹钟提醒
        self._manager.timerFinished.connect(self._on_timer_finished)

        tabs = QTabWidget()
        tabs.addTab(TasksPage(self._manager), "任务清单")
        tabs.addTab(TimerPage(self._manager), "计时")
        self.setCentralWidget(tabs)

    def _on_timer_finished(self, task: Task) -> None:
        TimerAlertDialog(task.name, self).exec()