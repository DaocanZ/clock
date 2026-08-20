"""计时页：选择一个任务，设置时长并启动醒目的倒计时。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .task import Task, TaskManager, format_ms


class TimerPage(QWidget):
    """大屏倒计时视图。选中任务 + 设定时长后开始，结束时用闹钟提示完成该任务。"""

    def __init__(self, manager: TaskManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._selected_id: str | None = None
        self._suppress = False

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("计时")
        title.setStyleSheet("QLabel { font-size: 22px; font-weight: bold; }")
        root.addWidget(title)

        # 选择任务行
        picker = QHBoxLayout()
        picker.addWidget(QLabel("任务："))
        self._combo = QComboBox()
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        picker.addWidget(self._combo, 1)

        # 时长控件直接绑定任务 total_seconds，和任务清单页同步
        picker.addWidget(QLabel("时长："))
        self._min_spin = QSpinBox()
        self._min_spin.setRange(0, 999)
        self._min_spin.setSuffix(" 分")
        self._min_spin.valueChanged.connect(self._on_duration_editing)
        picker.addWidget(self._min_spin)
        self._sec_spin = QSpinBox()
        self._sec_spin.setRange(0, 59)
        self._sec_spin.setSuffix(" 秒")
        self._sec_spin.valueChanged.connect(self._on_duration_editing)
        picker.addWidget(self._sec_spin)
        root.addLayout(picker)

        # 大屏倒计时区
        card = QVBoxLayout()
        self._task_label = QLabel("—")
        self._task_label.setAlignment(Qt.AlignCenter)
        self._task_label.setStyleSheet("QLabel { font-size: 18px; color: #666; }")
        card.addWidget(self._task_label)

        self._countdown_label = QLabel("00:00")
        self._countdown_label.setAlignment(Qt.AlignCenter)
        self._countdown_label.setStyleSheet(
            "QLabel { font-size: 84px; font-weight: bold; font-family: Consolas;"
            " color: #1f6feb; }"
        )
        card.addWidget(self._countdown_label)
        root.addLayout(card, 1)

        # 控制按钮
        controls = QHBoxLayout()
        controls.addStretch(1)
        self._toggle_btn = QPushButton("开始")
        self._toggle_btn.setMinimumSize(110, 44)
        self._toggle_btn.clicked.connect(self._on_toggle)
        controls.addWidget(self._toggle_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.setMinimumSize(90, 44)
        self._reset_btn.clicked.connect(self._on_reset)
        controls.addWidget(self._reset_btn)
        controls.addStretch(1)
        root.addLayout(controls)

        # 数据信号
        manager.taskAdded.connect(self._reload_combo)
        manager.taskRemoved.connect(self._on_task_removed)
        manager.taskUpdated.connect(self._on_task_updated)
        manager.timerFinished.connect(self._on_timer_finished)

        self._reload_combo()

    # ---------- 事件 ----------
    def _reload_combo(self) -> None:
        current = self._combo.currentData()
        self._combo.blockSignals(True)
        self._combo.clear()
        for task in self._manager.tasks:
            self._combo.addItem(task.name, task.id)
        # 尽量保持原选择
        idx = self._combo.findData(current) if current else 0
        self._combo.setCurrentIndex(max(0, idx))
        self._combo.blockSignals(False)
        self._on_selection_changed()

    def _on_task_removed(self, task_id: str) -> None:
        if self._selected_id == task_id:
            self._selected_id = None
        self._reload_combo()

    def _on_selection_changed(self) -> None:
        self._selected_id = self._combo.currentData()
        task = self._selected()
        if task is None:
            self._task_label.setText("—")
            self._countdown_label.setText("00:00")
            return
        self._task_label.setText(task.name)
        self._sync_duration_spins(task)
        self._render(task)

    def _on_task_updated(self, task: Task) -> None:
        if task.id == self._selected_id:
            self._task_label.setText(task.name)
            self._sync_duration_spins(task)
            self._render(task)

    def _selected(self) -> Task | None:
        if self._selected_id is None:
            return None
        return self._manager.get(self._selected_id)

    # ---------- 时长同步 ----------
    def _sync_duration_spins(self, task: Task | None) -> None:
        """把任务总时长同步到本页 分/秒 控件（抑制回环）。运行中禁用。"""
        if task is None or task.running:
            self._min_spin.setEnabled(False)
            self._sec_spin.setEnabled(False)
            return
        self._min_spin.setEnabled(True)
        self._sec_spin.setEnabled(True)
        mins, secs = task.total_seconds // 60, task.total_seconds % 60
        self._suppress = True
        if self._min_spin.value() != mins:
            self._min_spin.setValue(mins)
        if self._sec_spin.value() != secs:
            self._sec_spin.setValue(secs)
        self._suppress = False

    def _on_duration_editing(self) -> None:
        if self._suppress:
            return
        task = self._selected()
        if task is None or task.running:
            return
        total = self._min_spin.value() * 60 + self._sec_spin.value()
        if total != task.total_seconds:
            self._manager.set_duration(task, total)

    def _on_toggle(self) -> None:
        task = self._selected()
        if task is None:
            return
        if task.total_seconds <= 0:
            # 从当前输入应用时长（valueChanged 通常已同步，这里兜底）
            if not task.running:
                self._on_duration_editing()
            task = self._selected()
            if task is None or task.total_seconds <= 0:
                return
        if task.running:
            self._manager.pause(task)
        else:
            self._manager.start(task)

    def _on_reset(self) -> None:
        task = self._selected()
        if task is not None:
            self._manager.reset(task)

    def _render(self, task: Task) -> None:
        self._countdown_label.setText(format_ms(task.remaining_ms))
        if task.running:
            self._toggle_btn.setText("暂停")
        elif task.remaining_ms > 0:
            self._toggle_btn.setText("继续")
        else:
            self._toggle_btn.setText("开始")

    def _on_timer_finished(self, task: Task) -> None:
        if task.id == self._selected_id:
            self._render(task)
        TimerAlertDialog(task.name, self).exec()