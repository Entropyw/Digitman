import sys
import threading
from ssh import connect_to_server, send_message_and_get_response
from speech_service import SpeechService
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QLineEdit,
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter, QPen, QBrush, QColor, QPixmap

if not connect_to_server():
    print("无法连接到服务器，程序退出")
    sys.exit(1)

def count_characters(text):
    chinese_count = 0
    english_count = 0
    for char in text:
        if "\u4e00" <= char <= "\u9fff" or "\u3000" <= char <= "\u303f" or "\uff00" <= char <= "\uffa0":
            chinese_count += 1
        elif char.isalpha() and char.isascii():
            english_count += 1
    return chinese_count * 2 + english_count

class MicrophoneButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(50, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #7289DA;
                border-radius: 25px;
                border: none;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("white"), 2)
        brush = QBrush(QColor("white"))
        painter.setPen(pen)
        painter.setBrush(brush)
        body_rect = QRect(20, 13, 10, 20)
        painter.drawRoundedRect(body_rect, 5, 5)
        painter.drawLine(20, 35, 30, 35)
        body_rect1 = QRect(24, 33, 2, 8)
        painter.drawRect(body_rect1)

class CameraButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(50, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #7289DA;
                border-radius: 25px;
                border: none;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("white"), 2)
        brush = QBrush(QColor("white"))
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRoundedRect(QRect(15, 15, 20, 15), 3, 3)
        painter.drawEllipse(25, 17, 8, 8)
        painter.drawRect(17, 13, 5, 3)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("black"), 2))
        painter.drawEllipse(20, 16, 10, 10)

class ChatGUI(QWidget):
    addMessageSignal = pyqtSignal(str, bool, int)

    def __init__(self):
        super().__init__()
        self.CHARACTER_IMAGE_PATH = Path(__file__).resolve().parent / "character.png"
        self.speech_service = SpeechService()
        self.stop_event = None
        self.initUI()
        self.addMessageSignal.connect(self.add_message)

    def initUI(self):
        self.setWindowTitle("聊天界面")
        self.setFixedSize(800, 500)
        self.setStyleSheet("background-color: #2C2F33;")
        self.setWindowIcon(QIcon())

        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)
        self.setLayout(root_layout)

        chat_column = QVBoxLayout()
        chat_column.setSpacing(10)
        root_layout.addLayout(chat_column, 1)

        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                padding: 10px;
            }
            QListWidget::item {
                background-color: transparent;
            }
        """)
        self.chat_list.setWordWrap(True)
        self.chat_list.setSpacing(5)
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.chat_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chat_column.addWidget(self.chat_list)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入你的消息...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #23272A;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #7289DA;
                color: white;
                border-radius: 5px;
                padding: 5px 10px;
            }
        """)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)
        chat_column.addLayout(input_layout)

        self.send_button.clicked.connect(self.on_send_button_clicked)

        self.mic_button = MicrophoneButton()
        self.camera_button = CameraButton()
        self.stop_button = QPushButton("■")
        self.stop_button.setFixedSize(50, 50)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5555;
                color: white;
                font-size: 24px;
                border-radius: 25px;
                border: none;
            }
        """)
        self.stop_button.setVisible(False)

        # 修改按钮布局，避免按钮重叠
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.mic_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.camera_button)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.stop_button)
        button_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        chat_column.addLayout(button_layout)

        self.mic_button.clicked.connect(self.on_mic_button_clicked)
        self.stop_button.clicked.connect(self.on_stop_button_clicked)

        self.character_panel = QLabel()
        self.character_panel.setObjectName("characterPanel")
        self.character_panel.setFixedWidth(280)
        self.character_panel.setMinimumHeight(400)
        self.character_panel.setAlignment(Qt.AlignCenter)
        self.character_panel.setStyleSheet("""
            QLabel#characterPanel {
                background-color: #232428;
                border-radius: 20px;
                border: 2px solid #444;
            }
        """)

        pixmap = QPixmap(str(self.CHARACTER_IMAGE_PATH))
        if not pixmap.isNull():
            self.character_panel.setPixmap(
                pixmap.scaled(260, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.character_panel.setText("[Missing character.png]")
            self.character_panel.setStyleSheet(
                self.character_panel.styleSheet() + "color: #FF8888; font-size: 18px; padding: 10px;"
            )

        root_layout.addWidget(self.character_panel)
        self.bootstrap_demo_messages()

    def showEvent(self, event):
        super().showEvent(event)
        self.animation = QPropertyAnimation(self.mic_button, b"geometry")
        self.animation.setDuration(1000)
        self.animation.setLoopCount(-1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        initial_geometry = self.mic_button.geometry()
        self.animation.setStartValue(initial_geometry)
        self.animation.setEndValue(initial_geometry.adjusted(2, 2, -2, -2))

    def add_message(self, text, is_ai=True, item_index=None):
        if item_index is None:
            # Create new dialog box
            item = QListWidgetItem()
            message_widget = QWidget()
            message_layout = QHBoxLayout()
            message_layout.setSpacing(8)

            avatar = QLabel("🤖" if is_ai else "😊")
            avatar.setFixedSize(40, 40)
            avatar.setStyleSheet("""
                QLabel {
                    background-color: #FFFFFF;
                    color: #000000;
                    font-size: 24px;
                    border-radius: 20px;
                    border: 2px solid #555555;
                    text-align: center;
                }
            """)
            avatar.setAlignment(Qt.AlignCenter)

            label = QLabel(text)
            label.setWordWrap(True)
            sizet = count_characters(text)
            label.setStyleSheet("""
                QLabel {
                    background-color: %s;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 20px;
                    font-size: 16px;
                    min-width: %dpx;
                }
            """ % ("#7289DA" if is_ai else "#4CAF50", 360 if sizet >= 42 else sizet * 9))
            label.setMinimumSize(label.sizeHint())
            label.setMaximumWidth(600)

            if is_ai:
                message_layout.addWidget(avatar)
                message_layout.addWidget(label)
                message_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding))
            else:
                message_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding))
                message_layout.addWidget(label)
                message_layout.addWidget(avatar)

            message_widget.setLayout(message_layout)
            item.setSizeHint(message_widget.sizeHint())
            self.chat_list.addItem(item)
            self.chat_list.setItemWidget(item, message_widget)
        else:
            # Update existing dialog box
            item = self.chat_list.item(item_index)
            message_widget = self.chat_list.itemWidget(item)
            label = message_widget.findChild(QLabel)
            current_text = label.text()
            new_text = current_text + " " + text
            label.setText(new_text)
            sizet = count_characters(new_text)
            label.setStyleSheet("""
                QLabel {
                    background-color: %s;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 20px;
                    font-size: 16px;
                    min-width: %dpx;
                }
            """ % ("#7289DA" if is_ai else "#4CAF50", 360 if sizet >= 42 else sizet * 9))
            label.setMinimumSize(label.sizeHint())
            item.setSizeHint(message_widget.sizeHint())
        message_widget.setLayout(message_layout)
        message_widget.setStyleSheet("background-color: transparent;")
        item.setSizeHint(message_widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, message_widget)

        self.chat_list.scrollToBottom()
        self.chat_list.update()

    def on_send_button_clicked(self):
        text = self.input_box.text().strip()
        if text:
            self.addMessageSignal.emit(text, False, None)
            self.input_box.clear()
            threading.Thread(
                target=self.handle_ai_response, args=(text,), daemon=True
            ).start()

    def on_mic_button_clicked(self):
        self.mic_button.setEnabled(False)
        self.stop_button.setVisible(True)
        self.animation.start()
        self.stop_event = threading.Event()
        self.recognition_thread = threading.Thread(
            target=self.speech_service.real_time_speech_to_text,
            args=(self.on_speech_recognized, self.stop_event),
            daemon=True
        )
        self.recognition_thread.start()

    def on_stop_button_clicked(self):
        self.mic_button.setEnabled(True)
        self.stop_button.setVisible(False)
        self.animation.stop()
        if self.stop_event:
            self.stop_event.set()
            self.recognition_thread.join()

    def on_speech_recognized(self, text):
        self.addMessageSignal.emit(text, False, None)
        threading.Thread(
            target=self.handle_ai_response, args=(text,), daemon=True
        ).start()

    def handle_ai_response(self, text):
        response_generator = send_message_and_get_response(text)
        if response_generator:
            for output in response_generator:
                self.addMessageSignal.emit(output, True, None)
                QApplication.processEvents()  # 确保实时更新 UI

    def new_dialog(self):
        self.chat_list.clear()
        self.bootstrap_demo_messages()

    def bootstrap_demo_messages(self):
        self.addMessageSignal.emit("你好！有什么可以帮助你的吗？", True, None)

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = ChatGUI()
    window.show()
    sys.exit(app.exec_())