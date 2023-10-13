'''
# Author/s: Julio Arévalo Gómez, Gonzalo Arévalo Gómez
# Email: julioaregom02@gmail.com , gonzalo.arevalo.gomez@gmail.com
# Project: FyCUS23 / 2023 Edition
# License: GNU General Public License, version 3 (GPL-3.0)
'''

import serial

class RotatorPacket:
    header: str
    value1: str
    value2: str
    value3: str

    def __init__(self, _header: str, _value1: str, _value2: str = None, _value3: str = None):
        self.header = _header
        self.value1 = _value1
        self.value2 = _value2
        self.value3 = _value3

    def serialize(self) -> str:
        return f"${self.header}{self.value1}{',' + self.value2 if self.value2 is not None else ''},@"
    
    def __str__(self) -> str:
        return self.header + self.value1 + self.value2 + self.value3
        
class RotatorIOHandler:
    
    _serial: serial
    _offset: str

    def __init__(self, _serial_port: str, _baud_rate: int):
        self.serial = serial.Serial(port= _serial_port, baudrate=_baud_rate, timeout=1)

    def send(self, packet: RotatorPacket):
        print(f"Sent: {packet.serialize()}")
        self.serial.write(packet.serialize().encode())
            
    def receive(self) -> RotatorPacket:
        buffer=[]
        dataFlag=0
        while self.serial.in_waiting:          
            incomingByte=self.serial.read()
            if (incomingByte==b'#'):
                dataFlag=1
            
            if (incomingByte==b'&' and dataFlag==1):
                self.serial.reset_input_buffer()
                dataFlag=0
                if (buffer[1]=='S' and buffer[2]=='D'):
                    buffer=''.join(buffer)
                    parts = buffer.split(",")
                    return RotatorPacket(parts[0], parts[1], parts[2], parts[3])
                
            else:
                if dataFlag==1:
                    buffer.append(incomingByte.decode())
