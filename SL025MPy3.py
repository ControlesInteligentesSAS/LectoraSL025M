#!/usr/bin/python

#http://www.stronglink-rfid.com/download/SL025M-User-Manual.pdf

import serial

def byteToInteger(x):

    return int.from_bytes(x,'little')

def integerToByte(x):
    return x.to_bytes(1, 'little')

def CRC(Data):
    """
    Verificación de redundancia cíclica
    """
    lrc = 0
    for v in Data:
        lrc ^= v
    return lrc

TYPES= {b'\x01' : 'Mifare 1k, 4 byte UID',
    b'\x02' : 'Mifare 1k, 7 byte UID',
    b'\x03' : 'Mifare UltraLight or NATG203, 7 byte UID',
            b'\x04' : 'Mifare 4k, 4 byte UID',
            b'\x05' : 'Mifare 4k, 7 byte UID',
            b'\x06' : 'Mifare DesFire, 7 byte UID',
            b'\x0A' : 'Other'}

STATUS = {b'\x00' : 'Success',
            b'\x01' : 'No tag',
            b'\x02' : 'Login succeed',
            b'\x03' : 'Login fail',
            b'\x04' : 'Read fail',
            b'\x05' : 'Write fail',
            b'\x06' : 'Unable to read after write',
            b'\x08' : 'Address overflow',
            b'\x09' : 'Download Key fail',
            b'\x0D' : 'No authenticate',
            b'\x0E' : 'Not a value block',
            b'\x0F' : 'Invaled len of command format',
            b'\xF0' : 'Checksum error',
            b'\xF1' : 'Command code error'}

def findPort():
    import serial.tools.list_ports as ports
    ports = list(ports.comports())
    thePort=False
    i=0
    while not thePort:
        p=ports[i]
        ser=serial.Serial(port=p[0],baudrate=9600,timeout=0.5,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
        SELECTCMD=bytearray(b'\xBA\x02\x01')
        SELECTCMD.append(CRC(SELECTCMD))
        ser.write(SELECTCMD)
        response = ser.readline()
        if integerToByte(response[0]) == b'\xBD':
            thePort=p[0]
        i+=1
    return thePort




def selectCard(port):
    """
    Selecciona la tarjeta y devuelve el UID y el tipo de tarjeta"""
    ser = serial.Serial(
            port=port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        timeout=1
    )
    SELECTCMD=bytearray(b'\xBA\x02\x01')
    SELECTCMD.append(CRC(SELECTCMD))
    ser.write(SELECTCMD)
    response = ser.readline()
    if integerToByte(response[0]) == b'\xBD':
        status=STATUS[integerToByte(response[3])]
        print(f"Status: {status}")
        if status=="Success":
            length=response[1]
            ttype=TYPES[integerToByte(response[length])]
            uid=response[4:length-2].hex() #As the different cards have different UID lengths, we need to parse the UID differently
            checksum=response[9]
            print(f"UID: {uid}")
            print(f"Type: {ttype}")
            if checksum == CRC(response[0:9]):
                print("CRC OK")
            return {'uid':uid,'type':integerToByte(response[length]),'literalType':ttype}
    else:
        return "ERR","port_conn","connecting port", port
#C09B3755B261
def loginSector(port,sector,type,key):
    pass