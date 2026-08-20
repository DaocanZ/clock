"""任务数据模型与全局倒计时计时逻辑。"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, QTimer, Signal

# 全局计时心跳间隔（毫秒）。越小显示越平滑。
TICK_MS = 200


@dataclass
class Task:
    """单个任务及其倒计时状态。"""
    name: str = "未命名任务"
    total_seconds: int = 0          # 配置的倒计时总秒数
    remaining_ms: int = 0           # 当前剩余毫秒
    running: bool = False           # 是否正在倒计时
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    end_monotonic: float = 0.0      # 倒计时到达的单调时钟（仅在 running 时有意义）

    def remember_end(self) -> None:
        """开始/继续倒计时时记录结束时刻。"""
        self.end_monotonic = time.monotonic() + self.remaining_ms / 1000.0


class TaskManager(QObject):
    """管理任务列表，并用单个心跳计时器驱动所有进行中的倒计时。"""

    taskAdded = Signal(object)          # 参数：Task
    taskRemoved = Signal(str)           # 参数：task_id
    taskUpdated = Signal(object)        # 参数：Task（name/时长/剩余被修改）
    timerFinished = Signal(object)      # 参数：Task（倒计时归零）

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tasks: list[Task] = []
        self.ringtone_path: str = ""
        self._file = self._data_file()
        self._tick = QTimer(self)
        self._tick.setInterval(TICK_MS)
        self._tick.timeout.connect(self._on_tick)
        self.load()

    @staticmethod
    def _data_file() -> Path:
        """返回持久化数据文件路径。"""
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        folder = Path(base)
        folder.mkdir(parents=True, exist_ok=True)
        return folder / "my_clock_data.json"

    # ---------- 持久化 ----------
    def load(self) -> None:
        """从本地文件恢复任务清单与铃声设置。"""
        if not self._file.exists():
            return
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
            for item in data.get("tasks", []):
                task = Task(name=str(item.get("name", "未命名任务")))
                task.total_seconds = int(item.get("total_seconds", 0))
                task.remaining_ms = task.total_seconds * 1000
                self._tasks.append(task)
            self.ringtone_path = str(data.get("ringtone", ""))
        except (json.JSONDecodeError, OSError, ValueError):
            # 数据损坏时忽略，保留空清单
            pass

    def save(self) -> None:
        try:
            data = {
                "tasks": [
                    {"name": t.name, "total_seconds": t.total_seconds}
                    for t in self._tasks
                ],
                "ringtone": self.ringtone_path,
            }
            self._file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def set_ringtone(self, path: str | None) -> None:
        self.ringtone_path = path or ""
        self.save()

    # ---------- 任务管理 ----------
    def add_task(self, name: str) -> Task:
        task = Task(name=name)
        self._tasks.append(task)
        self.taskAdded.emit(task)
        self.save()
        return task

    def remove_task(self, task_id: str) -> None:
        task = next((t for t in self._tasks if t.id == task_id), None)
        if task is None:
            return
        self._tasks.remove(task)
        self.taskRemoved.emit(task_id)
        self.save()

    def get(self, task_id: str) -> Task | None:
        return next((t for t in self._tasks if t.id == task_id), None)

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    # ---------- 计时控制 ----------
    def set_duration(self, task: Task, total_seconds: int) -> None:
        """设置（未运行任务的）倒计时总时长，并重置剩余时间。"""
        total_seconds = max(0, int(total_seconds))
        task.total_seconds = total_seconds
        task.remaining_ms = total_seconds * 1000
        task.running = False
        self.taskUpdated.emit(task)
        self.save()

    def set_name(self, task: Task, name: str) -> None:
        task.name = name
        self.taskUpdated.emit(task)
        self.save()

    def start(self, task: Task) -> None:
        if task.remaining_ms <= 0:
            task.remaining_ms = task.total_seconds * 1000
        task.remember_end()
        task.running = True
        if not self._tick.isActive():
            self._tick.start()
        self.taskUpdated.emit(task)

    def pause(self, task: Task) -> None:
        if task.running:
            task.remaining_ms = max(0, int((task.end_monotonic - time.monotonic()) * 1000))
        task.running = False
        self._maybe_stop_ticker()
        self.taskUpdated.emit(task)

    def reset(self, task: Task) -> None:
        task.running = False
        task.remaining_ms = task.total_seconds * 1000
        self._maybe_stop_ticker()
        self.taskUpdated.emit(task)

    def _maybe_stop_ticker(self) -> None:
        if not any(t.running for t in self._tasks):
            self._tick.stop()

    def _on_tick(self) -> None:
        now = time.monotonic()
        for task in self._tasks:
            if not task.running:
                continue
            remaining = (task.end_monotonic - now) * 1000
            if remaining <= 0:
                task.remaining_ms = 0
                task.running = False
                self.taskUpdated.emit(task)
                self.timerFinished.emit(task)
            else:
                task.remaining_ms = int(remaining)
                self.taskUpdated.emit(task)
        self._maybe_stop_ticker()


def format_ms(ms: int) -> str:
    """把毫秒格式化为 HH:MM:SS 或 MM:SS。"""
    ms = max(0, int(ms))
    total = int(ms / 1000)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"