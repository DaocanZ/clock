"""倒计时闹钟提醒对话框：倒计时结束时提示要完成任务。"""
from __future__ import annotations

import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if sys.platform == "win32":
    import winsound


class TimerAlertDialog(QDialog):
    """全屏幕置顶的闹钟提醒，重复响铃直到用户点击"知道了"。"""

    def __init__(self, task_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("时间到")
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint
        )
        self.setModal(True)
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("⏰ 时间到！")
        title.setStyleSheet("QLabel { font-size: 40px; font-weight: bold; color: #d1242f; }")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        body = QLabel(f"倒计时结束，现在请完成任务：\n\n<b>{task_name}</b>")
        body.setTextFormat(Qt.RichText)
        body.setStyleSheet("QLabel { font-size: 20px; }")
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(body)

        btn = QPushButton("知道了")
        btn.setMinimumHeight(40)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

        # 重复响铃，直到对话框关闭
        self._beep = QTimer(self)
        self._beep.setInterval(800)
        self._beep.timeout.connect(self._ring)
        self._beep.start()
        self._ring()

    def _ring(self) -> None:
        if sys.platform == "win32":
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                return
            except Exception:
                pass
        from PySide6.QtWidgets import QApplication

        QApplication.beep()