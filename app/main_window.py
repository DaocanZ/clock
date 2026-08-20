"""主窗口：聚合任务清单页与计时页，并提供铃声设置菜单。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFileDialog,
    QLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QTabWidget,
)

from .alert import TimerAlertDialog
from .mini_window import MiniClockWindow
from .task import Task, TaskManager
from .tasks_page import TasksPage
from .timer_page import TimerPage

AUDIO_FILTER = "音频文件 (*.wav *.mp3 *.ogg *.flac *.m4a);;所有文件 (*)"

# 允许窗口自由缩放的最小尺寸（接近零）
MIN_WINDOW_SIZE = (0, 0)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("我的时钟")
        self.resize(760, 560)
        # 取消最小尺寸限制：允许自由拉伸到很小
        self.setMinimumSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])

        self._manager = TaskManager(self)
        # 任何任务倒计时结束都弹出闹钟提醒
        self._manager.timerFinished.connect(self._on_timer_finished)
        self._mini: MiniClockWindow | None = None

        tabs = QTabWidget()
        tabs.addTab(TasksPage(self._manager), "任务清单")
        tabs.addTab(TimerPage(self._manager), "计时")
        self.setCentralWidget(tabs)
        # 取消最小尺寸限制：布局不强制派生最小尺寸，允许任意缩小
        self.centralWidget().setMinimumSize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])
        if self.layout() is not None:
            self.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self._build_toolbar()
        self._build_menu(self.menuBar())

    def _build_toolbar(self) -> None:
        """顶部工具条：提供醒目的"切换小窗"按钮（模仿微软时钟紧凑模式）。"""
        tb = self.addToolBar("视图")
        tb.setMovable(False)
        tb.setFloatable(False)
        toggle = tb.addAction("⤢ 切换小窗")
        toggle.setToolTip("切换到始终置顶的小窗，小窗内可再回到主窗口")
        toggle.triggered.connect(self._toggle_mini)

    def _build_menu(self, menubar: QMenuBar) -> None:
        settings = menubar.addMenu("设置")

        choose = settings.addAction("选择闹钟铃声…")
        choose.triggered.connect(self._choose_ringtone)

        ringtone = settings.addAction("恢复默认铃声")
        ringtone.triggered.connect(self._clear_ringtone)

        settings.addSeparator()

        mini = settings.addAction("切换小窗模式")
        mini.triggered.connect(self._toggle_mini)

        settings.addSeparator()

        info = settings.addAction("关于")
        info.triggered.connect(self._show_about)

    def _choose_ringtone(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择闹钟铃声", "", AUDIO_FILTER
        )
        if not path:
            return
        self._manager.set_ringtone(path)
        QMessageBox.information(
            self,
            "铃声已设置",
            "铃声已保存。倒计时结束时将播放该音频。",
        )

    def _clear_ringtone(self) -> None:
        self._manager.set_ringtone("")
        QMessageBox.information(self, "铃声已恢复", "已恢复为默认系统提示音。")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "关于 我的时钟",
            "我的时钟 —— 任务清单 + 倒计时闹钟\n\n"
            "每个任务可设置倒计时，结束时弹出提醒并播放铃声。\n\n"
            "数据自动保存在本机，重启应用不丢失。",
        )

    def _toggle_mini(self) -> None:
        """在主窗口与小窗之间互斥切换（两者不同时出现）。"""
        if self._mini is not None and self._mini.isVisible():
            self._exit_mini()
        else:
            self._enter_mini()

    def _enter_mini(self) -> None:
        if self._mini is None:
            self._mini = MiniClockWindow(self._manager, self._exit_mini)
        # 隐藏主窗口，显示始终置顶小窗
        self.hide()
        self._mini.show()
        self._mini.raise_()

    def _exit_mini(self) -> None:
        # 隐藏小窗，切回主窗口
        if self._mini is not None:
            self._mini.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_timer_finished(self, task: Task) -> None:
        TimerAlertDialog(task.name, self, self._manager.ringtone_path).exec()