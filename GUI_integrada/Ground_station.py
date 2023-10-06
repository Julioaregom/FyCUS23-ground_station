import multiprocessing as mp
import matplotlib.pyplot as plt
import sys, time, keyboard, struct, random
import numpy as np

import socket
import numpy as np
import multiprocessing as mp
import threading as th
import bus_packet as bp
import src.globals as GLOBALS

from src.rotatorConnectController import RotatorConnectController
from src.displayPanel import displayPanel
from PyQt5 import QtWidgets


# UPD default config
DEFAULT_HOST = "192.168.1.1"
DEFAULT_PORT = 2023

float2bytes = lambda x: struct.pack('f', float(x))
bytes2float = lambda x: struct.unpack('f', bytes(x))[0]
bytes2uint = lambda x: struct.unpack('<H', bytes(x))[0]
bytes2int = lambda x: struct.unpack('<h', bytes(x))[0]


def decodeTM(data):
    pos = 2
    last_pos = pos
    ret = list()
    if(data.data[0] & bp.REQUIRED_DATA_GNSS):
        last_pos = pos
        pos+=18
        gnss = [bytes2nmea(data.data[last_pos:pos])]
        ret.append(gnss)
    
    if(data.data[0] & bp.REQUIRED_DATA_ACELL):
        last_pos = pos
        pos+=2
        accel_x = bytes2int(data.data[last_pos:pos])
        last_pos = pos
        pos+=2
        accel_y = bytes2int(data.data[last_pos:pos])
        last_pos = pos
        pos+=2
        accel_z = bytes2int(data.data[last_pos:pos])
        ret.append([accel_x,accel_y,accel_z])

    if(data.data[0] & bp.REQUIRED_DATA_GYRO):
        last_pos = pos
        pos+=2
        gyro_x = bytes2int(data.data[last_pos:pos])
        last_pos = pos
        pos+=2
        gyro_y = bytes2int(data.data[last_pos:pos])
        last_pos = pos
        pos+=2
        gyro_z = bytes2int(data.data[last_pos:pos])
        ret.append([gyro_x,gyro_y,gyro_z])

    if(data.data[0] & bp.REQUIRED_DATA_MAGNETOMETER):
        last_pos = pos
        pos+=2
        mag_x = bytes2int(data.data[last_pos:pos])
        last_pos = pos
        pos+=2
        mag_y = bytes2int(data.data[last_pos:pos])
        last_pos = pos
        pos+=2
        mag_z = bytes2int(data.data[last_pos:pos])
        ret.append([mag_x,mag_y,mag_z])              

    if(data.data[0] & bp.REQUIRED_DATA_PRESSURE):
        last_pos = pos
        pos+=4
        pressure = bytes2float(data.data[last_pos:pos])
        ret.append(pressure)  

    if(data.data[0] & bp.REQUIRED_DATA_TEMPERATURE_OUTDOOR):
        last_pos = pos
        pos+=4
        t = bytes2float(data.data[last_pos:pos])
        ret.append(t)

    if(data.data[0] & bp.REQUIRED_DATA_TEMPERATURE_UP):
        last_pos = pos
        pos+=4
        t = bytes2float(data.data[last_pos:pos])
        ret.append(t)
        
    if(data.data[0] & bp.REQUIRED_DATA_TEMPERATURE_BATTERY):
        last_pos = pos
        pos+=4
        t = bytes2float(data.data[last_pos:pos])
        ret.append(t)
        
    if(data.data[1] & (bp.REQUIRED_DATA_TEMPERATURE_DOWN>>8)):
        last_pos = pos
        pos+=4
        t = bytes2float(data.data[last_pos:pos])
        ret.append(t) 

    if(data.data[1] & (bp.REQUIRED_DATA_PV_VOLTAGE>>8)):
        last_pos = pos
        pos+=2
        pvV = bytes2uint(data.data[last_pos:pos])
        ret.append(pvV)    
    
    if(data.data[1] & (bp.REQUIRED_DATA_PV_CURRENT>>8)):
        last_pos = pos
        pos+=2
        pvA = bytes2uint(data.data[last_pos:pos])
        ret.append(pvA) 
    
    if(data.data[1] & (bp.REQUIRED_DATA_BATTERY_VOLTAGE>>8)):
        last_pos = pos
        pos+=2
        batV = bytes2uint(data.data[last_pos:pos])
        ret.append(batV) 

    if(data.data[1] & (bp.REQUIRED_DATA_BATTERY_CURRENT>>8)):
        last_pos = pos
        pos+=2
        batA = bytes2uint(data.data[last_pos:pos])
        ret.append(batA) 

    if(data.data[1] & (bp.REQUIRED_DATA_BATTERY_CHARGING>>8)):
        last_pos = pos
        pos+=2
        batCh = bytes2uint(data.data[last_pos:pos])
        ret.append(batCh) 

    if(data.data[1] & (bp.REQUIRED_DATA_BATTERY_DIETEMP>>8)):
        last_pos = pos
        pos+=2
        batDie = bytes2uint(data.data[last_pos:pos])
        ret.append(batDie) 

    if(data.data[1] & (bp.REQUIRED_DATA_CURRENT_TIME>>8)):
        last_pos = pos
        pos+=4
        time = bytes2float(data.data[last_pos:pos])
        ret.append(time) 
    return ret



def bytes2nmea(data):
    lat = bytes2float(data[0:4])
    ns = data[4]
    lon = bytes2float(data[5:9])
    ew = data[9]
    alt = bytes2float(data[10:14])
    sep = bytes2float(data[14:18])

    return [lat, ns, lon, ew, alt, sep]

def nmea2geodetic(data):
    lat_aux=data[0]/100
    lat_deg=np.trunc(lat_aux)
    lat_min=lat_aux-lat_deg
    lat=lat_deg+lat_min/60

    lon_aux=data[2]/100
    lon_deg=np.trunc(lon_aux)
    lon_min=lon_aux-lon_deg
    lon=lon_deg+lon_min/60

    data[0]=lat
    data[2]=lon  
    return data



def th_tcp_tx (sock, data_out_buffer):
    """Envía los datos de la cola de salida por TCP"""
    while True:
        try:
            data = data_out_buffer.get()
            sock.send(bytes(data))
        except:
            break


def th_tcp_rx (sock, data_in_buffer):
    """
    Recibe los datos por TCP y los pone en la cola de entrada.
    Si la codificación falla, no se ponen en la cola.
    """
    while True:
        try:
            data_udp_in, address = sock.recvfrom(500)
            
            # Debugging
            print(f"Data received: {list(data_udp_in)}")
            
            status, packet = bp.bus_packet_Decode(data_udp_in)   
            if status == 0:
                data_in_buffer.put(packet)
            else:
                print("Error al decodificar los datos recibidos")  
            
        except:
            break


def mp_modem (data_in_buffer, data_out_buffer):
    """
    Conecta con el modem por TCP/IP y pone los datos recibidos en la cola de entrada.
    Acordarse de configurar el host y el puerto.
    """
    while True:
        host = DEFAULT_HOST
        port = DEFAULT_PORT

        # Conectar socket TCP/IP (puedes hacerlo UDP)
        print("Conectando con el modem...")
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, port))
                print("Conexión establecida")
                break
            except:
                print("Error en la conexión TCP/IP")
                print("Reconectando en 3 segundos...")
                time.sleep(3)
            


        # Un hilo para enviar y otro para recibir, así no bloquean el proceso la lectura de TCP/IP(RX) y la de colas(TX)
        th_send = th.Thread(target=th_tcp_tx, args=(sock, data_out_buffer))   
        th_recv = th.Thread(target=th_tcp_rx, args=(sock, data_in_buffer))
        th_send.start(), th_recv.start()

        # Checkear estado constantemente para no perder la conexión
        while True:
            time.sleep(2)
            if not th_send.is_alive() or not th_recv.is_alive():
                print("Error en la conexión TCP/IP")
                print("Reconectando...")
                sock.close()
                break
        
    
    

def mp_data_process(data_in, data_gnss, data_tm_tmtc_buffer):
    """
    Procesa los datos recibidos y decide qué hacer con ellos.
    Si hay datos de GNSS, los pone en la cola de GNSS.
    Siempre guarda los datos en un archivo csv.
    """
    while True:
        try:
           
            # buffer FIFO (saca el primer elemento que entró)
            data = data_in.get()
            
            # Debugging
            print(f"Data received:")
            print(f"\tPacket Type: {data.packet_type}")
            print(f"\tAPID: {data.apid}")
            print(f"\tECF Flag: {data.ecf_flag}")
            print(f"\tLength: {data.length}")
            print(f"\tData: {list(data.data[:data.length-bp.BUS_PACKET_HEADER_SIZE-bp.BUS_PACKET_ECF_SIZE])}")
            print(f"\tECF: {data.ecf}")
            print("\n")
            
            # Procesalo
            if(data.packet_type == bp.BUS_PACKET_TYPE_TM):
                
                telemetry = decodeTM(data)
                data_gnss.put(telemetry[0])
                print(telemetry)              
               
            data_tm_tmtc_buffer.put(data)

            # SIEMPRE guardar datos en archivo txt
            
            with open('data.csv', "a") as file:
                file.write(time.strftime("%H:%M:%S") + "," + str(data.packet_type) + "," + str(data.apid) + "," + str(data.ecf_flag) + "," + str(data.length) + ",")
                for i in range(data.length-bp.BUS_PACKET_HEADER_SIZE-bp.BUS_PACKET_ECF_SIZE):
                    file.write(str(data.data[i]) + ",")
                file.write(str(data.ecf) + "\n")
                file.close()
                pass
    
        except:
            print("Error en el procesamiento de datos")
            pass
    


def gnss_buffer_get(data_gnss_buffer):
    while True:
        try:
            gnss_data = data_gnss_buffer.get()
            gnss_data= gnss_data[0]
            gnss_data[1]=chr(gnss_data[1])
            gnss_data[3]=chr(gnss_data[3])
            gnss_data=nmea2geodetic(gnss_data)
            GLOBALS.GLOBAL_GNSS=gnss_data
        except:
            pass
        
        
def mp_antenna(data_gnss_buffer):
    """
    GUI de la antena.
    A completar por Julio.
    """

    app = QtWidgets.QApplication(sys.argv)
    exit_status = 1 # Bad exit 


    while exit_status == 1:
        gps_connect_window = RotatorConnectController(data_gnss_buffer)
        exit_status = app.exec_() # 0 if normal exit

    sys.exit()





def gui_tmtc(_tm_tmtc_buffer,_tc_buffer):
    """
    GUI de TM/TC.
    A completar por Julio.
    """    
    app = QtWidgets.QApplication(sys.argv)
    gps_connect_window = displayPanel(_tm_tmtc_buffer, _tc_buffer)
    sys.exit(app.exec_())

    




if __name__ == '__main__':
    tm_buffer = mp.Queue()
    tc_buffer = mp.Queue()
    gnss_buffer = mp.Queue()
    tm_tmtc_buffer = mp.Queue()


    # Se puede hacer con Threads o con Process, pero recomiendo hacer un Process al menos para el UDP
    mp_antenna_handle = mp.Process(name="Antena process", target=mp_antenna, args=([gnss_buffer]))
    mp_modem_handle = mp.Process(name="UDP read", target=mp_modem, args=(tm_buffer, tc_buffer))
    mp_data_process_handle = mp.Process(name="Data process", target=mp_data_process, args=(tm_buffer, gnss_buffer, tm_tmtc_buffer))
    mp_modem_handle.start(), mp_data_process_handle.start(), mp_antenna_handle.start()

    try:
        gui_tmtc(tm_tmtc_buffer, tc_buffer)
        
    except KeyboardInterrupt:
            mp_modem_handle.terminate()
            mp_data_process_handle.terminate()
            mp_antenna_handle.terminate()
