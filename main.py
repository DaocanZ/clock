"""程序入口：运行"我的时钟"桌面应用。

用法：python main.py
"""
import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    # 固定应用名，确保持久化数据路径稳定（窗口标题另行设置）
    app.setOrganizationName("MyClock")
    app.setApplicationName("MyClock")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())