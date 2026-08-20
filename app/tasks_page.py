"""任务清单页：每个任务对应一个带倒计时控件的卡片行。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .task import Task, TaskManager, format_ms


class TaskItemWidget(QWidget):
    """单个任务的卡片行：可编辑名称 + 倒计时 + 控制按钮。"""

    deleteRequested = Signal(str)  # task_id

    def __init__(self, task: Task, manager: TaskManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._task = task
        self._manager = manager
        self._highlighted = False
        self._suppress = False
        self.setObjectName("taskRow")
        self.setStyleSheet(self._row_style(False))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        self._input = QLineEdit(task.name)
        self._input.setPlaceholderText("任务名称")
        self._input.editingFinished.connect(self._on_name_changed)
        layout.addWidget(self._input, 4)

        # 时长设置：分 + 秒（直接绑定到任务的 total_seconds，改动即同步）
        self._min_spin = QSpinBox()
        self._min_spin.setRange(0, 999)
        self._min_spin.setSuffix(" 分")
        self._min_spin.setEnabled(not task.running)
        self._min_spin.valueChanged.connect(self._on_duration_editing)
        layout.addWidget(self._min_spin)
        self._sec_spin = QSpinBox()
        self._sec_spin.setRange(0, 59)
        self._sec_spin.setSuffix(" 秒")
        self._sec_spin.setEnabled(not task.running)
        self._sec_spin.valueChanged.connect(self._on_duration_editing)
        layout.addWidget(self._sec_spin)
        if task.total_seconds:
            self._min_spin.setValue(task.total_seconds // 60)
            self._sec_spin.setValue(task.total_seconds % 60)

        self._time_label = QLabel(format_ms(task.remaining_ms))
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setFixedWidth(110)
        time_style = (
            "QLabel { font-size: 20px; font-weight: bold; color: #1f6feb;"
            " font-family: Consolas; }"
        )
        self._time_label.setStyleSheet(time_style)
        layout.addWidget(self._time_label)

        self._toggle_btn = QPushButton("开始" if not task.running else "暂停")
        self._toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self._toggle_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.clicked.connect(lambda: self._manager.reset(self._task))
        layout.addWidget(self._reset_btn)

        self._done_btn = QPushButton()
        self._done_btn.clicked.connect(self._on_toggle_done)
        layout.addWidget(self._done_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setToolTip("删除此任务")
        delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self._task.id))
        layout.addWidget(delete_btn)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("QLabel { color: #e3b341; font-weight: bold; }")
        layout.addWidget(self._status_label)

    @staticmethod
    def _row_style(highlighted: bool) -> str:
        if highlighted:
            return (
                "QWidget#taskRow { background: #e6f4ea;"
                " border: 2px solid #2ea043; border-radius: 8px; }"
            )
        return ""

    def _on_toggle_done(self) -> None:
        self._manager.mark_complete(self._task, not self._task.completed)

    def _sync_duration_spins(self) -> None:
        """把任务的总时长同步到本行动 时 分 秒控件（抑制回环）。"""
        if self._task.running:
            return
        mins = self._task.total_seconds // 60
        secs = self._task.total_seconds % 60
        self._suppress = True
        if self._min_spin.value() != mins:
            self._min_spin.setValue(mins)
        if self._sec_spin.value() != secs:
            self._sec_spin.setValue(secs)
        self._suppress = False

    def _on_duration_editing(self) -> None:
        if self._suppress or self._task.running:
            return
        total = self._min_spin.value() * 60 + self._sec_spin.value()
        if total != self._task.total_seconds:
            self._manager.set_duration(self._task, total)

    def refresh(self) -> None:
        """根据任务状态刷新显示。"""
        self._time_label.setText(format_ms(self._task.remaining_ms))
        running = self._task.running
        done = self._task.completed

        # 已完成：灰色去强调、取消绿色高亮
        highlight = running and not done
        if highlight != self._highlighted:
            self._highlighted = highlight
            self.setStyleSheet(self._row_style(highlight))

        # 名称样式：已完成加删除线
        font = self._input.font()
        font.setStrikeOut(done)
        self._input.setFont(font)

        # 按钮：已完成时禁用计时控件，按钮切换为"恢复"
        enable = not running and not done
        self._min_spin.setEnabled(enable)
        self._sec_spin.setEnabled(enable)
        self._toggle_btn.setEnabled(not done)
        self._reset_btn.setEnabled(not done)
        self._done_btn.setText("恢复" if done else "完成")
        if not running and not done:
            self._sync_duration_spins()

        if done:
            self._toggle_btn.setText("开始")
            self._status_label.setText("已完成")
            self._status_label.setStyleSheet("QLabel { color: #9aa5b1; font-weight: bold; }")
        elif running:
            self._toggle_btn.setText("暂停")
            self._status_label.setText("进行中…")
            self._status_label.setStyleSheet("QLabel { color: #2ea043; font-weight: bold; }")
        elif self._task.running is False and self._task.remaining_ms > 0:
            self._toggle_btn.setText("继续")
            self._status_label.setText("已暂停")
            self._status_label.setStyleSheet("QLabel { color: #e3b341; font-weight: bold; }")
        else:
            self._toggle_btn.setText("开始")
            self._status_label.setText("")
            self._status_label.setStyleSheet("QLabel { color: #2ea043; font-weight: bold; }")
            if self._task.total_seconds and self._task.remaining_ms <= 0:
                self._status_label.setText("已结束")
                self._status_label.setStyleSheet("QLabel { color: #d1242f; font-weight: bold; }")

    def _on_toggle(self) -> None:
        if self._task.running:
            self._manager.pause(self._task)
            return
        # 先确保已设置时长
        total = self._min_spin.value() * 60 + self._sec_spin.value()
        if total != self._task.total_seconds:
            self._manager.set_duration(self._task, total)
        self._manager.start(self._task)

    def _on_name_changed(self) -> None:
        name = self._input.text().strip()
        if not name:
            self._input.setText(self._task.name)
            return
        self._manager.set_name(self._task, name)


class TasksPage(QWidget):
    """展示任务清单；支持新增、删除，每个任务带独立倒计时闹钟。"""

    def __init__(self, manager: TaskManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._rows: dict[str, TaskItemWidget] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel("任务清单")
        title.setStyleSheet("QLabel { font-size: 22px; font-weight: bold; }")
        root.addWidget(title)
        root.addSpacing(6)

        # 新增任务条
        add_row = QHBoxLayout()
        self._add_input = QLineEdit()
        self._add_input.setPlaceholderText("输入任务名称，回车或点击添加…")
        self._add_input.returnPressed.connect(self._add_task)
        add_row.addWidget(self._add_input, 1)
        add_btn = QPushButton("＋ 添加任务")
        add_btn.clicked.connect(self._add_task)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)
        root.addSpacing(10)

        self._plist = QListWidget()
        self._plist.setSelectionMode(QListWidget.NoSelection)
        root.addWidget(self._plist, 1)

        hint = QLabel("提示：选中任务名称后输入时长后点击“开始”即可倒计时；倒计时结束会有闹钟提醒。")
        hint.setStyleSheet("QLabel { color: #888; }")
        root.addWidget(hint)

        # 连接数据源信号
        manager.taskAdded.connect(self._on_task_added)
        manager.taskRemoved.connect(self._on_task_removed)
        manager.taskUpdated.connect(lambda _task: self._refresh_row(_task.id))

        for task in manager.tasks:
            self._on_task_added(task)

    def _add_task(self) -> None:
        name = self._add_input.text().strip()
        if not name:
            return
        self._manager.add_task(name)
        self._add_input.clear()

    def _on_task_added(self, task: Task) -> None:
        item = QListWidgetItem()
        widget = TaskItemWidget(task, self._manager)
        widget.deleteRequested.connect(self._manager.remove_task)
        item.setSizeHint(widget.sizeHint())
        self._plist.addItem(item)
        self._plist.setItemWidget(item, widget)
        self._rows[task.id] = widget

    def _on_task_removed(self, task_id: str) -> None:
        widget = self._rows.pop(task_id, None)
        if widget is None:
            return
        for i in range(self._plist.count()):
            if self._plist.itemWidget(self._plist.item(i)) is widget:
                self._plist.takeItem(i)
                break

    def _refresh_row(self, task_id: str) -> None:
        widget = self._rows.get(task_id)
        if widget is not None:
            widget.refresh()