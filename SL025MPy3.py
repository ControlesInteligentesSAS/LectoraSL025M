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
    retorno=False
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
    """Lee un bloque de datos

    Args:
        ser (str): Puerto donde está conectada la lectora
        block (int): [Dirección del bloque que se va a leer]
        
    Returns:
        bytearray: [Retorna el bloque de datos si la operacion es exitosa]
    """ 
    try:
        READCMD=bytearray(b'\xBA\x03\x03')
        READCMD.append(block)
        READCMD.append(CRC(READCMD))
        response=sendCommand(ser,READCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Read data block failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def writeDataBlock(ser:serial,block:int,data:list)->bytearray:
    """Escribe un bloque de datos

    Args:
        ser (str): Puerto donde está conectada la lectora
        block (int): [Dirección del bloque que se va a escribir]
        data (list): Los datos que se van a escribir
        
    Returns:
        bytearray: [Retorna el bloque de datos escrito si la operacion es exitosa]
    """ 
    try:
        WRITECMD=bytearray(b'\xBA\x13\x04')
        WRITECMD.append(block)
        for k in data:
            WRITECMD.append(k)
        WRITECMD.append(CRC(WRITECMD))
        response=sendCommand(ser,WRITECMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Write data block failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        return (str(e))
    finally:
        pass

def readValueBlock(ser:serial,block:int)->bytearray:
    """Lee el valor de un bloque

    Args:
        ser (str): Puerto donde está conectada la lectora
        block (int): [Dirección del bloque que se va a leer]
        
    Returns:
        bytearray: [Retorna el valor si la operacion es exitosa]
    """ 
    try:
        READCMD=bytearray(b'\xBA\x03\x05')
        READCMD.append(block)
        READCMD.append(CRC(READCMD))
        response=sendCommand(ser,READCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Read value block failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def inicializeValueblock(ser:serial,block:int,value:list)->bytearray:
    """Inicializa el valor de un bloque

    Args:
        ser (str): Puerto donde está conectada la lectora
        block (int): [Dirección del bloque que se va a inicializar]
        value (list): [El valor a escribir]
        
    Returns:
        bytearray: [Retorna el valor escrito si la operacion es exitosa]
    """ 
    try:
        INITCMD=bytearray(b'\xBA\x07\x06')
        INITCMD.append(block)
        for k in value:
            INITCMD.append(k)
        INITCMD.append(CRC(INITCMD))
        response=sendCommand(ser,INITCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Inicialize value failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def writeMasterKey(ser:serial,sector:bytes,key:bytes)->bytearray:
    """Escribe la llave maestra

    Args:
        ser (str): Puerto donde está conectada la lectora
        sector (bytes): [Numero del sector que se va a escribir, 0x00-0x27]
        key (bytes): [Llave de autenticacion]
        
    Returns:
        bytearray: [Retorna la llave de autenticacion escrita si la operacion es exitosa]
    """ 
    try:
        WRITECMD=bytearray(b'\xBA\x09\x07'+sector+key)
        WRITECMD.append(CRC(WRITECMD))
        response=sendCommand(ser,WRITECMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Write master key failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        return (str(e))
    finally:
        pass

def incrementValue(ser:serial,block:int,value:list)->bytearray:
    """Incrementa el valor

    Args:
        ser (str): Puerto donde está conectada la lectora
        block (int): [Dirección del bloque que se va a incrementar]
        value (list): [El valor a ser incrementado]
        
    Returns:
        bytearray: [Retorna el valor despues del incremento si la operacion es exitosa]
    """ 
    try:
        INCREMCMD=bytearray(b'\xBA\x07\x08')
        INCREMCMD.append(block)
        for k in value:
            INCREMCMD.append(k)
        INCREMCMD.append(CRC(INCREMCMD))
        response=sendCommand(ser,INCREMCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Increment value failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def decrementValue(ser:serial,block:int,value:list)->bytearray:
    """Incrementa el valor

    Args:
        ser (str): Puerto donde está conectada la lectora
        block (int): [Dirección del bloque que se va a decrementar]
        value (list): [El valor a ser decrementado]
        
    Returns:
        bytearray: [Retorna el valor despues del decremento si la operacion es exitosa]
    """ 
    try:
        DECREMCMD=bytearray(b'\xBA\x07\x09')
        DECREMCMD.append(block)
        for k in value:
            DECREMCMD.append(k)
        DECREMCMD.append(CRC(DECREMCMD))
        response=sendCommand(ser,DECREMCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Decrement value failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def copyValue(ser:serial,source:int,destination:int)->bytearray: #PENDIENTE
    """Copia el valor

    Args:
        ser (str): Puerto donde está conectada la lectora
        source (int): [Fuente desde donde el bloque se va a copiar]
        destination (int): [Destino a donde se va a copiar]
        La fuente y el destino deben estar en el mismo sector
        
    Returns:
        bytearray: [Retorna el valor despues de la copia si la operacion es exitosa]
    """ 
    try:
        COPYCMD=bytearray(b'\xBA\x04\x0A')
        COPYCMD.append(source)
        COPYCMD.append(destination)
        COPYCMD.append(CRC(COPYCMD))
        print(COPYCMD)
        response=sendCommand(ser,COPYCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Copy value failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def readDataPage(ser:serial,page:int)->bytearray:
    """Lee una pagina de datos (UltraLight & NTAG203)

    Args:
        ser (str): Puerto donde está conectada la lectora
        page (int): [Numero de página a leer, 0x00-0x0F]
        
    Returns:
        bytearray: [Retorna el bloque de datos si la operacion es exitosa]
    """ 
    try:
        READCMD=bytearray(b'\xBA\x03\x10')
        READCMD.append(page)
        READCMD.append(CRC(READCMD))
        print(READCMD)
        response=sendCommand(ser,READCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Read data page failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def writeDataPage(ser:serial,page:int,data:list)->bytearray: #PENDIENTE
    """Escribe una pagina de datos (UltraLight & NTAG203)

    Args:
        ser (str): Puerto donde está conectada la lectora
        page (int): [Numero de página a escribir, 0x00-0x0F]
        data (list): [Los datos a escribir]
        
    Returns:
        bytearray: [Retorna los datos de la pagina escrita si la operacion es exitosa]
    """
    try:
        WRITECMD=bytearray(b'\xBA\x07\x11')
        WRITECMD.append(page)
        for k in data:
            WRITECMD.append(k)
        WRITECMD.append(CRC(WRITECMD))
        print(WRITECMD)
        response=sendCommand(ser,WRITECMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Write data page failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

def manageRedLed(ser:serial,code:bytes)->bool:
    """Manejo del led rojo

    Args:
        ser (str): Puerto donde está conectada la lectora
        code (int): [0 para led apagado, otro para led encendido]
        
    Returns:
        bool: [Retorna True si la sesión fue exitosa, False si no]
    """
    retorno= False
    try:
        MANAGECMD=bytearray(b'\xBA\x03\x40'+code)
        MANAGECMD.append(CRC(MANAGECMD))
        response=sendCommand(ser,MANAGECMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Manage red led failed! {STATUS[integerToByte(response[3])]}")
            else:
                retorno = True
                return retorno
    except Exception as e:
        pass
    finally:
        return retorno

def getFimwareVersion(ser:serial)->bytearray:
    """Se obtiene la version del Fimware

    Args:
        ser (str): Puerto donde está conectada la lectora
                
    Returns:
        bytearray: [Retorna la version del fimware si la operacion es exitosa]
    """
    try:
        GETCMD=bytearray(b'\xBA\x02\xF0')
        GETCMD.append(CRC(GETCMD))
        response=sendCommand(ser,GETCMD)
        print(response)
        if integerToByte(response[0]) == b'\xBD':
            if response[3] != 0:
                raise Exception(f"Get fimware version failed! {STATUS[integerToByte(response[3])]}")
            else:
                return response[4:]
    except Exception as e:
        pass
    finally:
        pass

serialObject=getSerialObject()
loginSector(serialObject,b'\x01',b'\xAA',hexToBytes("852D76D7634E"))
#selectCard(findPort())
#(b'\r\xaa\x115\xa0\xcf')
downloadKeyIntoReader(serialObject,b'\x01',b'\xAA',hexToBytes("852D76D7634E"))
loginSectorStoredKey(serialObject,b'\x01',b'\xAA')

# respuesta=(readDataBlock(serialObject,1))
# respuesta2=[]
# for k in respuesta:
#     respuesta2.append(k)
# def byteToHex(byte:bytes)->str:
#     return ''.join(format(b, '02x') for b in byte)
# print("LECTURAA")
# print(byteToHex(respuesta))
# print(respuesta)
# print(respuesta2)

# respuesta2=[146, 9, 250, 113, 19, 7, 0, 1, 0, 0, 0, 0, 2, 1, 0, 0, 171]
# respuesta2.pop()
# escritura=(writeDataBlock(serialObject,1,respuesta2))
# print("ESCRITURA")
# print(escritura)

# readValue= readValueBlock(serialObject,2)
# print(readValue)

#value=[32,54,67,5]
# inicializeValue = inicializeValueblock(serialObject,1,value)
# print(inicializeValue)

# writeKey=writeMasterKey(serialObject,b'\x00',hexToBytes("C09B3755B261"))
# print(writeKey)

# value=[32,54,67,5]
# incrementV = incrementValue(serialObject,2,value)
# print(incrementV)

# value=[32,54,67,5]
# decrementV = decrementValue(serialObject,1,value)
# print(decrementV)

# copyV = copyValue(serialObject,0,0)
# print("VALOR")
# print(copyV)

# readDP = readDataPage(serialObject,1)
# print(readDP)
# res=[]
# for k in readDP:
#     res.append(k)

# res.pop()
# print(res)

# data=[4,3,2,5]
# writeDP = writeDataPage(serialObject,1,data)
# print(writeDP)

# manageLed = manageRedLed(serialObject,b'\x01')
# print(manageLed)

# getFimware= getFimwareVersion(serialObject)
# print(getFimware)




# arreglo=[]
# for k in respuesta:
#     arreglo.append(k)
# print(arreglo)
# print(integerToByte(9))
# print(byteToInteger(b'\x12'))
# print(integerToByte(4))

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
    