#!/usr/bin/python

#http://www.stronglink-rfid.com/download/SL025M-User-Manual.pdf

import serial

def byteToInteger(x):
    return int.from_bytes(x,'little')

def integerToByte(x):
    return x.to_bytes(1, 'little')


def CRC(Data:bytes)->bytes:
    """
    Verificación de redundancia cíclica
    """
    lrc = 0
    for v in Data:
        lrc ^= v
    return lrc

def getSerialObject(port:str)->serial.serialwin32.Serial:
    """[Obtiene el objeto serial para la conexión con la lectora]

    Args:
        port (str): [El puerto donde está conectada la lectora]

    Returns:
        serial.serialwin32.Serial: [Objeto serial para la conexión con la lectora]
    """    
    return serial.Serial(
        port=port,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )
    

def hexToBytes(hex:str)->bytes:
    return bytes.fromhex(hex)


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
    """[Devuelve el puerto que está conectado a la tarjeta]

    Returns:
        [string]: [El puerto en el cuál está conectada la consola]
    """    
    import serial.tools.list_ports as ports
    ports = list(ports.comports())
    thePort=False
    i=0
    while not thePort:
        p=ports[i]
        ser=getSerialObject(p[0])
        SELECTCMD=bytearray(b'\xBA\x02\x01')
        SELECTCMD.append(CRC(SELECTCMD))
        ser.write(SELECTCMD)
        response = ser.readline()
        if integerToByte(response[0]) == b'\xBD':
            thePort=p[0]
        i+=1
    return thePort

def sendCommand(port:str,command:bytearray)->bytearray:
    """[Envia un comando a la lectora]

    Args:
        command (bytearray): [El comando a enviar]

    Returns:
        bytearray: [El arreglo de bytes que responde la lectora]
    """    
    response=bytearray()
    try:
        ser = getSerialObject(port)
        ser.write(command)
        response=ser.readline()
        status = STATUS[integerToByte(response[3])]
        print(f"Response status: {status}")
        checksum=response[:-1]
        print(f"the checksum is {checksum} and the CRC is {CRC(response)}")
        if checksum == CRC(response):
            print("Checksum OK")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        return response


def selectCard(port:str):
    """Selecciona la tarjeta que está sobre la lectora

    Args:
        port (str): [El puerto donde está conectada la lectora]

    Returns:
        [dict]: [Diccionario con el uuid y el tipo de tarjeta en hexadecimal y literal]
    """        
    try:
        SELECTCMD=bytearray(b'\xBA\x02\x01')
        SELECTCMD.append(CRC(SELECTCMD))
        print(f"Sending select command {SELECTCMD}")
        response = sendCommand(port,SELECTCMD)
        if integerToByte(response[0]) == b'\xBD':
            status=STATUS[integerToByte(response[3])]
            if status=="Success":
                length=response[1]
                print(f"Length of response: {length}, response: {response}")
                ttype=TYPES[integerToByte(response[length])]
                uid=response[4:length].hex() #As the different cards have different UID lengths, we need to parse the UID differently
                checksum=response[9]
                print(f"UID: {uid}")
                print(f"UID in Decimal: {int(uid,16)}")
                print(f"Type: {ttype}")
                if checksum == CRC(response[0:9]):
                    print("CRC OK")
                return {'uid':uid,'type':integerToByte(response[length]),'literalType':ttype}
            else:
                raise Exception(f"{status}")
        else:
            return "ERR","port_conn","connecting port", port
    except Exception as e:
        print(f"Error: {str(e)}")
        
        
#C09B3755B261
def loginSector(port:str,sector:bytes,keyType:bytes,key:bytes)->bool:
    """Inicia sesión en un sector de la tarjeta

    Args:
        port (str): Puerto donde está conectada la lectora
        sector (bytes): [Sector a iniciar sesión]
        keyType (bytes): [Tipo de clave a usar (0xAA, 0xBB)]
        key (bytes): [Clave de inicio de sesión en bytes]

    Returns:
        bool: [Retorna True si la sesión fue exitosa, False si no]
    """ 
    retorno = False
    try:   
        LOGINCMD=bytearray(b'\xBA\n\x02'+sector+keyType+key)
        LOGINCMD.append(CRC(LOGINCMD))
        print(f"Sending login command {LOGINCMD}")
        response=sendCommand(port,LOGINCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            pass
    except Exception as e:
        print(f"Error {str(e)}")
    finally:
        return retorno

def downloadKeyIntoReader(port:str,sector:bytes,keyType:bytes,key:bytes)->bool:
    """Descarga una clave de la tarjeta

    Args:
        port (str): Puerto donde está conectada la lectora
        sector (bytes): [Sector a descargar la clave]
        keyType (bytes): [Tipo de clave a usar (0xAA, 0xBB)]
        key (bytes): [Clave a descargar en bytes]

    Returns:
        bool: [Retorna True si la sesión fue exitosa, False si no]
    """ 
    retorno = False
    try:   
        DOWNLOADCMD=bytearray(b'\xBA\n\x12'+sector+keyType+key)
        DOWNLOADCMD.append(CRC(DOWNLOADCMD))
        print(f"Sending download command {DOWNLOADCMD}")
        response=sendCommand(port,DOWNLOADCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            pass
    except Exception as e:
        print(f"Error {str(e)}")
    finally:
        return retorno

#selectCard(findPort())
#(b'\r\xaa\x115\xa0\xcf')
#loginSector(findPort(),b'\x00',b'\xAA',hexToBytes("0DAA1135A0CF"))
downloadKeyIntoReader(findPort(),b'\x00',b'\xAA',hexToBytes("C09B3755B261"))
#print(integerToByte(9))