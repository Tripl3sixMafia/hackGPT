import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from bear_fud import BearFudV4

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("BearFudV4")
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("BearFudV4")
        layout.addWidget(label)

        button = QPushButton("Run")
        button.clicked.connect(self.runBearFud)
        layout.addWidget(button)

        self.show()

    def runBearFud(self):
        bear_fud = BearFudV4()
        asyncio.run(bear_fud.run())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())