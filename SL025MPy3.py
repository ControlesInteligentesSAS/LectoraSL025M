#!/usr/bin/python

#http://www.stronglink-rfid.com/download/SL025M-User-Manual.pdf

"""
[Librería para utilización de la lectora SL025M]

Author @Juan Camacho
"""""""""

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
    

def hexToBytes(hex:str)->bytes:
    return bytes.fromhex(hex)

def getSerialObjectByPort(port:str)->serial.serialwin32.Serial:
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

def getSerialObject():
    """[Devuelve un objeto serial que tiene conexión con la lectora]

    Returns:
        [string]: [El objeto serial]
    """    
    import serial.tools.list_ports as ports
    ports = list(ports.comports())
    thePort=False
    i=0
    while not thePort and i<len(ports):
        p=ports[i]
        ser=getSerialObjectByPort(p[0])
        SELECTCMD=bytearray(b'\xBA\x02\x01')
        SELECTCMD.append(CRC(SELECTCMD))
        ser.write(SELECTCMD)
        response = ser.readline()
        if integerToByte(response[0]) == b'\xBD':
            thePort=ser
        i+=1
    return thePort

def sendCommand(ser:serial,command:bytearray)->bytearray:
    """[Envia un comando a la lectora]

    Args:
        command (bytearray): [El comando a enviar]

    Returns:
        bytearray: [El arreglo de bytes que responde la lectora]
    """    
    response=bytearray()
    try:
        ser.write(command)
        response=ser.readline()
        if len(response)==0:
            raise Exception("No response")
        status = STATUS[integerToByte(response[3])]
        print(f"Response status: {status}")
        length=response[1]
        checksum=response[length+1]
        if not (checksum == CRC(response[0:length+1])):
            raise Exception("Checksum error!")
    except Exception as e:
        print(f"Error: {str(e)} on response {response}")
    finally:
        return response


def selectCard(ser:serial):
    """Selecciona la tarjeta que está sobre la lectora

    Args:
        ser (serial): [El puerto donde está conectada la lectora]

    Returns:
        [dict]: [Diccionario con el uuid y el tipo de tarjeta en hexadecimal y literal]
    """        
    try:
        SELECTCMD=bytearray(b'\xBA\x02\x01')
        SELECTCMD.append(CRC(SELECTCMD))
        print(f"Sending select command {SELECTCMD}")
        response = sendCommand(ser,SELECTCMD)
        if integerToByte(response[0]) == b'\xBD':
            status=STATUS[integerToByte(response[3])]
            if status=="Success":
                length=response[1]
                print(f"Length of response: {length}, response: {response}")
                ttype=TYPES[integerToByte(response[length])]
                uid=response[4:length].hex() #As the different cards have different UID lengths, we need to parse the UID differently
                print(f"UID: {uid}")
                print(f"UID in Decimal: {int(uid,16)}")
                print(f"Type: {ttype}")
                return {'uid':uid,'type':integerToByte(response[length]),'literalType':ttype}
            else:
                raise Exception(f"{status}")
        else:
            return "ERR","port_conn","connecting port"
    except Exception as e:
        print(f"Error: {str(e)}")
        
        
#C09B3755B261
def loginSector(ser:serial,sector:bytes,keyType:bytes,key:bytes)->bool:
    """Inicia sesión en un sector de la tarjeta

    Args:
        ser (serial): Puerto donde está conectada la lectora
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
        response=sendCommand(ser,LOGINCMD)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 2:
                raise Exception(f"Login failed! {STATUS[integerToByte(response[3])]}")
            else:
                retorno = True
    except Exception as e:
        print(f"Error {str(e)}")
    finally:
        return retorno

def downloadKeyIntoReader(ser:str,sector:bytes,keyType:bytes,key:bytes)->bool:
    """Descarga una clave de la tarjeta

    Args:
        ser (str): Puerto donde está conectada la lectora
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
        response=sendCommand(ser,DOWNLOADCMD)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Download failed! {STATUS[integerToByte(response[3])]}")
            else:
                retorno = True
    except Exception as e:
        print(f"Error {str(e)}")
    finally:
        return retorno
    
def loginSectorStoredKey(ser:serial,sector:bytes,keyType:bytes)->bool:
    try:
        LOGINCMD=bytearray(b'\xBA\x04\x13'+sector+keyType)
        LOGINCMD.append(CRC(LOGINCMD))
        response=sendCommand(ser,LOGINCMD)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 2:
                raise Exception(f"Login failed! {STATUS[integerToByte(response[3])]}")
            else:
                retorno = True
    except Exception as e:
        print(f"Error {str(e)}")
    finally:
        return retorno

def readDataBlock(ser:serial,block:int)->bytearray:
    try:
        READCMD=bytearray(b'\xBA\x03\x03')
        READCMD.append(block)
        READCMD.append(CRC(READCMD))
        response=sendCommand(ser,READCMD)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Read failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

serialObject=getSerialObject()
#loginSector(serialObject,b'\x00',b'\xAA',hexToBytes("C09B3755B261"))
#selectCard(findPort())
#(b'\r\xaa\x115\xa0\xcf')
downloadKeyIntoReader(serialObject,b'\x00',b'\xAA',hexToBytes("055EAC1B6339"))
loginSectorStoredKey(serialObject,b'\x00',b'\xAA')
respuesta=(readDataBlock(serialObject,1))
respuesta2=[]
for k in respuesta:
    respuesta2.append(k)
def byteToHex(byte:bytes)->str:
    return ''.join(format(b, '02x') for b in byte)
print(byteToHex(respuesta))
print(respuesta2)
#arreglo=[]
#for k in respuesta:
    #arreglo.append(k)
#print(arreglo)
#print(integerToByte(9))
#print(byteToInteger(b'\x12'))
#print(integerToByte(4))

""" lista=[186,3,3,3]
bytelista=bytearray()
for i in lista:
    bytelista.append(i)
bytelista.append(CRC(bytelista))
print(bytelista)
print(sendCommand(serialObject,bytelista)) """

def processBufferTag(buffer):
    try:
        print("BUFF", buffer)
        if len(buffer)==18:
            print("Nueva versión")
            buff=buffer
            buffer[0]=0
            buffer[1]=0
            for i in range(2,len(buffer)):
                buffer[i]=buffer[i+2]
            buffer[14]=0
            valor = []
            for i in range(0,13):
                valor.append(buffer[i + 2])
            buffer[15]=CRC(valor, len(valor))
            buffer[16]=255
        print("Changed buffer", buffer,"Original buffer", buff)
        listaTagsDetectados = []
        while len(buffer>=17):
            TagCounter = 0
            longitud = len(buffer)
            index = 0
            datoCorrecto = 0
            for i in range(0,len(buffer)):
                index+=1
                if buffer[i]==0:
                    if ((i+1) <(longitud+1)):
                        if buffer[i+1]==0:
                            print("Hay dato correcto")
                            datoCorrecto=1
                            break
        if datoCorrecto == 1:
            TagCounter += 1
            TagBytes = []

    except Exception as e:
        print(f"Error {str(e)}")
    