'''
# Author/s: Gonzalo Arévalo Gómez
# Email: gonzalo.arevalo.gomez@gmail.com
# Project: FyCUS23 / 2023 Edition
# License: GNU General Public License, version 3 (GPL-3.0)
'''


import time, serial
import src.globals as GLOBALS

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QLineEdit, QVBoxLayout, QLabel, QPushButton, QDialog
from interfaces.rotatorConnectUi import Ui_rotatorConnect
from src.rotatorCPanelController import RotatorCPanelController
from src.RotatorIOController import RotatorIOHandler, RotatorPacket



class RotatorConnectController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rotatorConnectWindow = Ui_rotatorConnect()
        self.rotatorConnectWindow.setupUi(self)
        self.show()
        self.center()

        # Set parameters default configuration 
        self.baud_rate = GLOBALS.BAUD_RATE
        self.serial_port_name = GLOBALS.SERIAL_PORT

        self.setSignalSlots()

    def setSignalSlots(self):
        # Buttons
        self.rotatorConnectWindow.btnConnect.pressed.connect(self.btnConnectPressed)

        #Actions
        self.rotatorConnectWindow.actConfigure.triggered.connect(self.actConfigurePressed)


    #############################################
    ##### Buttons/Actions behaviour (Slots) #####
    #############################################


    def btnConnectPressed(self):
        try:
            self.rotator_handler = RotatorIOHandler(self.serial_port_name, self.baud_rate)
            self.rotator_handler._offset = self.rotatorConnectWindow.boxOffset.text()

            # Give time to load serial port
            for i in range(200):
                time.sleep(0.01)
                self.rotatorConnectWindow.progressBar.setValue(i + 1)
        
            # Send offset to rotator
            self.rotator_handler.send(RotatorPacket('OF', self.rotator_handler._offset))

            self.rotatorCPanelWindow = RotatorCPanelController(self.rotator_handler)
            self.close()
        except serial.SerialException as e:
            self.criticalMsgBox(e)
            return
        
    def actConfigurePressed(self):
        new_port, new_baud_rate = self.serialConfMsgBox()
        if (new_port and new_baud_rate) != None:
            self.serial_port_name = new_port
            self.baud_rate = new_baud_rate

    #########################################
    ######   Window layout helpers   ########
    #########################################

    def criticalMsgBox(self, e: Exception):
        msgBox = QMessageBox()
        msgBox.resize(400, 300)
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setText("An error ocurred attempting to connect:")
        msgBox.setInformativeText(e.__str__())
        msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
        msgBox.exec()

    def serialConfMsgBox(self):
        msgBox = QDialog()
        msgBox.setWindowTitle("Configure serial connection")
        msgBox.resize(300, 100)
        
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Introduce the new port and baud rate:"))

        line_edit_port = QLineEdit(self.serial_port_name)
        layout.addWidget(line_edit_port)

        line_edit_br = QLineEdit(str(self.baud_rate))
        layout.addWidget(line_edit_br)

        button = QPushButton("Accept")
        layout.addWidget(button)

        button.clicked.connect(msgBox.accept)

        msgBox.setLayout(layout)

        result = msgBox.exec_()

        if result == QDialog.Accepted:
            return line_edit_port.text(), int(line_edit_br.text())
        else:
            return None, None
        
    def center(self):
        frame_geo = self.frameGeometry()
        screen_geo = QApplication.desktop().screenGeometry().center()
        frame_geo.moveCenter(screen_geo)
        self.move(frame_geo.topLeft())