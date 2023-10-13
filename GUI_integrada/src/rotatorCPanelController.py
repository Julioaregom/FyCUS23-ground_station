import threading, time
import src.globals as GLOBALS
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QLineEdit, QLabel, QVBoxLayout, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import QCoreApplication
from interfaces.rotatorControlPanelUi import Ui_rotatorControlPanel
from src.RotatorIOController import RotatorIOHandler, RotatorPacket
from src.Gps2Rotator import Gps2Rotator

class RotatorCPanelController(QMainWindow):
    def __init__(self, _rotator_handler: RotatorIOHandler, _buffer):
        super().__init__()
        self.rotator_handler = _rotator_handler
        self.btnOnOff_state = False
        self.btnTrack_state = True
        self.stop_tracking_event = threading.Event()
        self.stop_read_event = threading.Event()
        self.stop_GPSread_event = threading.Event()
        self.gnss_buffer = _buffer

        self.retFlag=0
        self.end_el=0.0
        self.end_az=0.0

        self.rotatorCPanelWindow = Ui_rotatorControlPanel()
        self.rotatorCPanelWindow.setupUi(self)
        self.show()
        self.topRight()

        # Set parameters default configuration 
        self.tr_freq = GLOBALS.TR_SEND_FREQ
        self.ref_latitude = GLOBALS.REF_LAT
        self.ref_longitude = GLOBALS.REF_LON    
        self.ref_altitude = GLOBALS.REF_ALT

        self.setSignalSlots()
        self.launchInputRead()

    def setSignalSlots(self):
        # Buttons
        self.rotatorCPanelWindow.btnTrack.pressed.connect(self.btnTrackPressed)
        self.rotatorCPanelWindow.btnOnOff.pressed.connect(self.btnOnOffPressed)
        self.rotatorCPanelWindow.btnHome.pressed.connect(self.btnHomePressed)
        self.rotatorCPanelWindow.btnSend.pressed.connect(self.btnSendPressed)

        # Actions
        self.rotatorCPanelWindow.actTrSendFreq.triggered.connect(self.actConfigTrackingFreq)
        self.rotatorCPanelWindow.actRefCoords.triggered.connect(self.actConfigRefCoords)
        self.rotatorCPanelWindow.actReload.triggered.connect(self.actPannicMsgBox)

        #Events
        self.rotatorCPanelWindow.boxDataAz.textChanged.connect(lambda: self.eveTextEdited(3))
        self.rotatorCPanelWindow.boxDataEl.textChanged.connect(lambda: self.eveTextEdited(3))

        self.rotatorCPanelWindow.boxDataAz.returnPressed.connect(self.eveReturnPressed)
        self.rotatorCPanelWindow.boxDataEl.returnPressed.connect(self.eveReturnPressed)

    def closeEvent(self, event):
        '''
        @Overrides
        '''
        print("Closing interfaces...")
        #Gently stop possible running threads
        self.stop_read_event.set()
        self.stop_tracking_event.set()

        #Close serial connection before exiting
        self.rotator_handler.serial.close()
        event.accept()
   
    def pannicRestart(self):
        self.close()
        QCoreApplication.exit(1)


    #####################################
    ##### Buttons behaviour (Slots) #####
    #####################################

    def btnTrackPressed(self):
        self.btnTrack_state = not self.btnTrack_state #Toggle status
        if not self.btnTrack_state and self.btnOnOff_state: # Tracking mode
            self.trackingModeLayout()
            self.stop_tracking_event.clear()
            track_thread=threading.Thread(target=self.trackingThread, args=[self.tr_freq, self.stop_tracking_event])
            track_thread.start()
            
        else: # Manual mode
            self.manualModeLayout()
            self.stop_tracking_event.set()

    def btnHomePressed(self):
        self.rotator_handler.send(RotatorPacket('HM', 0))

    def btnSendPressed(self):
        if (self.rotatorCPanelWindow.boxDataAz.text() != "") or (self.rotatorCPanelWindow.boxDataEl.text() != ""):
            self.rotator_handler.send(RotatorPacket('PO', self.rotatorCPanelWindow.boxDataAz.text(), self.rotatorCPanelWindow.boxDataEl.text()))
    
    # def btnSendPressed2(self):
    #     if self.retFlag==0:
    #         self.rotator_handler.send(RotatorPacket('PO', '90', '50'))
    #         self.retFlag=1
    #     if self.retFlag==1:
    #         self.rotator_handler.send(RotatorPacket('PO', '0', '0'))
    #         self.retFlag=0




    def btnOnOffPressed(self):
        self.btnOnOff_state = not self.btnOnOff_state #Toggle status
        if self.btnOnOff_state: # Mode on
            self.OnModeLayout()
            self.rotator_handler.send(RotatorPacket('ON', '1'))
        else: # Mode off
            self.OffModeLayout()
            self.rotator_handler.send(RotatorPacket('ON', '0'))

    def actConfigTrackingFreq(self):
        new_freq = self.frequencyConfigurationMsgBox()
        if new_freq  != None:
            self.tr_freq = new_freq
       
    def actConfigRefCoords(self):
        new_lat, new_lon, new_alt = self.coordsConfigurationMsgBox()
        if (new_lat and new_lon and new_alt) != None:
            self.ref_latitude = new_lat
            self.ref_longitude = new_lon
            self.ref_altitude = new_alt

    def eveTextEdited(self, dot_pos: int):
        sender = self.sender()
        current_text = sender.text()
        current_text = ''.join(filter(str.isdigit, current_text))
        if len(current_text) > dot_pos and current_text[dot_pos] != '.':
            current_text = current_text[:dot_pos] + '.' + current_text[dot_pos:]
        sender.setText(current_text)

    def eveReturnPressed(self):
        sender = self.sender()
        current_text = sender.text()
        current_text = current_text.ljust(sender.maxLength(), '0')
        sender.setText(current_text)

    ########################################
    ####  Thread related (Status read)  ####
    ########################################

    def launchInputRead(self):
        status_thr = threading.Thread(target=self.statusReadThread,args=[self.stop_read_event], daemon=True)
        status_thr.start()
        GPSinfo_thr = threading.Thread(target=self.GPSReadThread,args=[self.stop_GPSread_event], daemon=True)
        GPSinfo_thr.start()
    
    def statusReadThread(self, stop_thread_event: threading.Event):
        stop_thread_event.clear()
        while not stop_thread_event.is_set():
            try:
                time.sleep(0.1)
                rt_packet: RotatorPacket = self.rotator_handler.receive()
                if rt_packet:
                    self.rotatorCPanelWindow.lblStatusAz.setText(rt_packet.value1)
                    self.rotatorCPanelWindow.lblStatusEl.setText(rt_packet.value2)
                    self.rotatorCPanelWindow.lblRotatorStatus.setText(self.translateRotatorStatus(rt_packet.value3))
            except:
                pass



    def GPSReadThread(self, stop_thread_event: threading.Event):
        def nmea2geodetic(data):
            import numpy as np
            lat_aux=data[0]/100
            lat_deg=np.trunc(lat_aux)
            lat_min=lat_aux-lat_deg
            lat=lat_deg+lat_min/60

            lon_aux=data[2]/100
            lon_deg=np.trunc(lon_aux)
            lon_min=lon_aux-lon_deg
            lon=lon_deg+lon_min/60

            data[0]=lat
            data[1]=chr(data[1])
            data[2]=lon  
            data[3]=chr(data[3])
            return data
        
        stop_thread_event.clear()
        while not stop_thread_event.is_set():
            try:
                gnss_data = self.gnss_buffer.get()[0]
                gnss_data_tr=nmea2geodetic(gnss_data)

                lat,latSign,lon,lonSign,altOrt,undGeoide=gnss_data_tr
                alt_error=False
                if latSign=='S':
                    lat=-lat
                elif latSign=='N':
                    pass

                if lonSign=='W':
                    lon=-lon
                elif lonSign=='E':
                    pass

                if altOrt*1!=0 and undGeoide*1!=0:
                    altEllip=altOrt+undGeoide
                elif altOrt*1==0 and undGeoide*1==0:
                    alt_error=True
                    altEllip=0.0
                
                # Imprimo datos de GPS
                self.rotatorCPanelWindow.lblLatitude.setText(str(round(lat,3)))
                self.rotatorCPanelWindow.lblLongitude.setText(str(round(lon,3)))
                if not alt_error:
                    self.rotatorCPanelWindow.lblAltitude.setText(str(round(altOrt,4)))
                else:
                    self.rotatorCPanelWindow.lblAltitude.setText('Sin est.')
                
                # Imprimo datos de Az,El, distancia
                az,el,range=Gps2Rotator(lat,lon,altEllip,self.ref_latitude,self.ref_longitude,self.ref_altitude)
                az=round(az,2)
                el=round(el,2)
                range=range/1000
                range=round(range,2)
                if el<0.0:
                    el=0.0

                if alt_error:
                    self.end_el=''
                else:
                    self.end_el=str(round(el))
                self.end_az=az
                
                self.rotatorCPanelWindow.lblStatusAuxAz.setText(str(az))
                self.rotatorCPanelWindow.lblStatusAuxEl.setText(str(el))
                self.rotatorCPanelWindow.lblStatusRange.setText(str(range))  
            except:
                pass

    def trackingThread(self, frequency: int, stop_event: threading.Event):
        while not stop_event.is_set():
            #TODO: adaptar este método para que funcione con el programa que envía Az y El
            if self.end_az or self.end_el:
                self.rotator_handler.send(RotatorPacket('PO',str(self.end_az), self.end_el))
            time.sleep(frequency)

    #################################################
    ######   Window layout modes and helpers   ######
    #################################################

    def manualModeLayout(self):
        self.rotatorCPanelWindow.btnTrack.setText("Track")
        self.rotatorCPanelWindow.btnSend.setEnabled(True)
        self.rotatorCPanelWindow.btnHome.setEnabled(True)
        self.rotatorCPanelWindow.boxDataAz.setEnabled(True)
        self.rotatorCPanelWindow.boxDataEl.setEnabled(True)
        
    def trackingModeLayout(self):
        self.rotatorCPanelWindow.btnTrack.setText("Manual")
        self.rotatorCPanelWindow.btnSend.setEnabled(False)
        self.rotatorCPanelWindow.btnHome.setEnabled(False)
        self.rotatorCPanelWindow.boxDataAz.setEnabled(False)
        self.rotatorCPanelWindow.boxDataEl.setEnabled(False)

    def OffModeLayout(self):
        self.rotatorCPanelWindow.btnOnOff.setText("On")
        self.rotatorCPanelWindow.boxDataAz.setEnabled(False)
        self.rotatorCPanelWindow.boxDataEl.setEnabled(False)
        self.rotatorCPanelWindow.lblStatusAz.setEnabled(False)
        self.rotatorCPanelWindow.lblStatusEl.setEnabled(False)
        self.rotatorCPanelWindow.txtStatusAz.setEnabled(False)
        self.rotatorCPanelWindow.txtStatusEl.setEnabled(False)
        self.rotatorCPanelWindow.lblStatusAuxAz.setEnabled(False)
        self.rotatorCPanelWindow.lblStatusAuxEl.setEnabled(False)
        self.rotatorCPanelWindow.lblStatusRange.setEnabled(False)
        self.rotatorCPanelWindow.txtStatusAuxAz.setEnabled(False)
        self.rotatorCPanelWindow.txtStatusAuxEl.setEnabled(False)
        self.rotatorCPanelWindow.txtStatusRange.setEnabled(False)
        self.rotatorCPanelWindow.txtRotatorStatus.setEnabled(False)
        self.rotatorCPanelWindow.lblRotatorStatus.setEnabled(False)
        self.rotatorCPanelWindow.btnSend.setEnabled(False)
        self.rotatorCPanelWindow.btnTrack.setEnabled(False)
        self.rotatorCPanelWindow.btnHome.setEnabled(False)

    def OnModeLayout(self):
        self.rotatorCPanelWindow.btnOnOff.setText("Off")
        self.rotatorCPanelWindow.boxDataAz.setEnabled(True)
        self.rotatorCPanelWindow.boxDataEl.setEnabled(True)
        self.rotatorCPanelWindow.lblStatusAz.setEnabled(True)
        self.rotatorCPanelWindow.lblStatusEl.setEnabled(True)
        self.rotatorCPanelWindow.txtStatusAz.setEnabled(True)
        self.rotatorCPanelWindow.txtStatusEl.setEnabled(True)
        self.rotatorCPanelWindow.txtStatusRange.setEnabled(True)
        self.rotatorCPanelWindow.lblStatusAuxAz.setEnabled(True)
        self.rotatorCPanelWindow.lblStatusAuxEl.setEnabled(True)
        self.rotatorCPanelWindow.lblStatusRange.setEnabled(True)
        self.rotatorCPanelWindow.txtStatusAuxAz.setEnabled(True)
        self.rotatorCPanelWindow.txtStatusAuxEl.setEnabled(True)
        self.rotatorCPanelWindow.txtRotatorStatus.setEnabled(True)
        self.rotatorCPanelWindow.lblRotatorStatus.setEnabled(True)
        self.rotatorCPanelWindow.btnSend.setEnabled(True)
        self.rotatorCPanelWindow.btnTrack.setEnabled(True)
        self.rotatorCPanelWindow.btnHome.setEnabled(True)

    def translateRotatorStatus(self, status: int) -> str:
        if status == '1':
            return "idle"
        elif status == '2':
            return "moving"
        elif status == '4':
            return "homing"
    
    def topRight(self):
        desktop_geo = QApplication.desktop().screenGeometry()
        self.move(desktop_geo.topRight() - self.rect().topRight())

    def center(self):
        frame_geo = self.frameGeometry()
        screen_geo = QApplication.desktop().screenGeometry().center()
        frame_geo.moveCenter(screen_geo)
        self.move(frame_geo.topLeft())
    
    def frequencyConfigurationMsgBox(self):
        msgBox = QDialog()
        msgBox.setWindowTitle("Configure frequency")
        msgBox.resize(300, 100)
        
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select the frequency (seconds):"))

        combo_box = QComboBox()
        combo_box.addItems(["1", "3", "15", "30"])
        combo_box.setCurrentText(str(self.tr_freq))
        layout.addWidget(combo_box)

        button = QPushButton("Accept")
        layout.addWidget(button)

        button.clicked.connect(msgBox.accept)

        msgBox.setLayout(layout)

        result = msgBox.exec_()

        if result == QDialog.Accepted:
            return int(combo_box.currentText())
        else:
            return None
    
    def coordsConfigurationMsgBox(self):
        msgBox = QDialog()
        msgBox.setWindowTitle("Configure coordinates")
        msgBox.resize(300, 200)
        
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Introduce the reference coordinates:"))

        layout.addWidget(QLabel("Latitude:"))

        line_edit_lat = QLineEdit(str(self.ref_latitude))
        layout.addWidget(line_edit_lat)

        layout.addWidget(QLabel("Longitude:"))

        line_edit_lon = QLineEdit(str(self.ref_longitude))
        layout.addWidget(line_edit_lon)

        layout.addWidget(QLabel("Altitude:"))

        line_edit_alt = QLineEdit(str(self.ref_altitude))
        layout.addWidget(line_edit_alt)

        button = QPushButton("Accept")
        layout.addWidget(button)

        button.clicked.connect(msgBox.accept)

        msgBox.setLayout(layout)

        result = msgBox.exec_()

        if result == QDialog.Accepted:
            return float(line_edit_lat.text()), float(line_edit_lon.text()), float(line_edit_alt.text())
        else:
            return None, None, None

    def actPannicMsgBox(self):
        msgBox = QMessageBox()
        msgBox.resize(400, 300)
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle("Restart application")
        msgBox.setText("Are you sure you want to restart the application?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        result = msgBox.exec()

        if result == QMessageBox.Yes:
            self.pannicRestart()