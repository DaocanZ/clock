"""倒计时闹钟提醒对话框：倒计时结束时提示要完成任务，并播放铃声。"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_WAV_EXTS = {".wav", ".wave"}
if sys.platform == "win32":
    import winsound


class TimerAlertDialog(QDialog):
    """全屏幕置顶的闹钟提醒，重复响铃直到用户点击"知道了"。

    铃声来源：若设置了自定义铃声文件则播放它，否则播放系统提示音。
    """

    def __init__(
        self,
        task_name: str,
        parent: QWidget | None = None,
        ringtone_path: str = "",
    ) -> None:
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

        self._player = None
        self._loop_timer = None
        self._stop_ringing()

        if ringtone_path and Path(ringtone_path).is_file():
            self._ring_with_file(ringtone_path)
        else:
            # 未设置自定义铃声：播放系统提示音并循环
            self._loop_timer = QTimer(self)
            self._loop_timer.setInterval(800)
            self._loop_timer.timeout.connect(self._system_beep)
            self._loop_timer.start()
            self._system_beep()

    # ---------- 铃声播放 ----------
    def _ring_with_file(self, path: str) -> None:
        ext = Path(path).suffix.lower()
        if sys.platform == "win32" and ext in _WAV_EXTS:
            # wav 直接用系统播放器循环
            try:
                winsound.PlaySound(
                    path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
                )
                return
            except Exception:
                pass
        # 其它格式（mp3 等）用 QtMultimedia 播放，并循环
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            self._player = QMediaPlayer(self)
            self._output = QAudioOutput(self)
            self._player.setAudioOutput(self._output)
            self._output.setVolume(1.0)
            self._player.mediaStatusChanged.connect(self._on_media_status)
            self._player.setSource(QUrl.fromLocalFile(path))
            self._player.play()
            return
        except Exception:
            pass
        # 播放失败则退回系统提示音
        self._system_beep()

    def _on_media_status(self, status) -> None:
        # 播放结束后自动重新播放，实现循环
        try:
            from PySide6.QtMultimedia import QMediaPlayer

            if status == QMediaPlayer.MediaStatus.EndOfMedia and self._player is not None:
                self._player.play()
        except Exception:
            pass

    @staticmethod
    def _system_beep() -> None:
        if sys.platform == "win32":
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                return
            except Exception:
                pass
        from PySide6.QtWidgets import QApplication

        QApplication.beep()

    def _stop_ringing(self) -> None:
        if self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass
            self._player = None
        if self._loop_timer is not None:
            self._loop_timer.stop()
            self._loop_timer = None
        if sys.platform == "win32":
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    def reject(self) -> None:
        self._stop_ringing()
        super().reject()

    def accept(self) -> None:
        self._stop_ringing()
        super().accept()