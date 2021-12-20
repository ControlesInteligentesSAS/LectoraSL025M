import SL025MPy3 as lib
from datetime import datetime

def byteToHex(byte:bytes)->str:
    return ''.join(format(b, '02x') for b in byte)

def twos_complement(val,bits)->int:
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)       
    return val  

def getSerialCard(serial)->int:
    selectC=lib.selectCard(serial)
    keySerial=selectC["uid"][6:8]+selectC["uid"][4:6]+selectC["uid"][2:4]+selectC["uid"][0:2] #Se invierte el patron de bits
    serialCard=int(keySerial,16)
    return serialCard

def conversiones(data:list):
    dataToHex=byteToHex(data) #Conversion binario a hex de la data
    dataToHex=dataToHex[:-2] #Se elimina el checksum de la data entrante
    dataToIntList=[] #Lista en formato int de la data
    for k in data:
        dataToIntList.append(k)
    dataToHexList=[] #Lista en formato Hex de la data
    for k in dataToIntList:
        dataToHexList.append(hex(k)[2:4])
    dataToIntList.pop()
    return dataToHex,dataToIntList,dataToHexList

def checkSumArray(dataBinDeco:list)->bool:
    checkSum=0
    for i in range(0,len(dataBinDeco)-2,1):
        checkSum=checkSum^dataBinDeco[i]

    if (checkSum == dataBinDeco[len(dataBinDeco)-2]):
        return True
    else:
        return False

def readData(data:list):
    versionData=False

    key=[]
    for x in range(4,8,1):
        key.append(data[x])
    
    dataBinDeco=[]
    for x in range (0,len(data),1):
        dataBinDeco.append(data[x]^key[x % len(key)])
    version=data[len(data)-1] & 7
    dataBinDeco[len(dataBinDeco)-1]=version

    checksum = checkSumArray(dataBinDeco)

    if checksum:
        versionData = True

    return versionData,dataBinDeco

def VersionData0(dataHex:list, dataInt:list, dataHexList:list,serial:int)->str:
    print("serialcard:", str(serial))
    print("Data:", dataHex.upper())
    time=dataHex[6:8]+dataHex[4:6]+dataHex[2:4]+dataHex[0:2]
    dateLong=twos_complement(int(time,16),32)
    cad=str(dateLong)
    for i in range(4,16,1):
        if i>3 and i<8:
            cad=cad+"-"+str(dataInt[i])
        elif i>7 and i<12:
            cad=cad+" "+dataHexList[i]
        elif i>11 and i<14: 
            cad=cad+"-"+str(dataInt[i])
        else:
            cad=cad+"."+str(dataInt[i])
    #datelong, segundos,byteConsola,byteTipo,bytesConvenios(5),bytePago,numerosPlaca(3) 
    return cad.upper()

def versionData1(data:list,dataHex:list,serial:int)->str:
    print("serialcard:", str(serial))
    print("Data:", dataHex.upper())
    dataToHexList=[]
    for k in data:
        dataToHexList.append(hex(k)[2:4])
    fecha2000=946702800 # Fecha de inicio en formato Epoch (2000/01/01 00:00:00 GMT-05:00)
    time=dataToHexList[3]+dataToHexList[2]+dataToHexList[1]+dataToHexList[0]
    time1=int(time,16)
    entrada=datetime.fromtimestamp(fecha2000+time1)
    convenios = str(data[6])+" "+str(data[5])+" "+str(data[4]) #REVISAR
    minToExit=str(data[7])
    tipo=str(data[9]>>3)
    estado=str(data[9]&7)
    consola=str(data[10])
    park=str(data[11])
    varios=str(data[12])
    free=str(data[13])
    if estado==1 or estado==2:
        #Redim Preverse bytesSerPagoConvenios (convenios)
        #fechaPagoSalida= fechaEntrada.AddSeconds(BitConverter.ToUInt32(bytesSerPagoConvenios, 0))
        fechaPagoSalida= ""
        if estado==1:
            return ("Entrada: {} Pagó: {} Min To Exit: {} Tipo: {} Estado: {} Consola: {} Park: {} Varios: {} Free: {}".format(entrada,fechaPagoSalida,minToExit,tipo,estado,consola,park,varios,free))    
        if estado==1:
            return ("Entrada: {} Salida: {} Min To Exit: {} Tipo: {} Estado: {} Consola: {} Park: {} Varios: {} Free: {}".format(entrada,fechaPagoSalida,minToExit,tipo,estado,consola,park,varios,free))    
    else:
        return ("Entrada: {} Convenios: {} Min To Exit: {} Tipo: {} Estado: {} Consola: {} Park: {} Varios: {} Free: {}".format(entrada,convenios,minToExit,tipo,estado,consola,park,varios,free))

def decodificar()->str:
    dataToHex,dataToIntList,dataToHexList = conversiones(data)
    serialCard = getSerialCard(serialObject)
    version,dataBin=readData(dataToIntList)
    decode = ""

    print("DECODE")
    if version==1:
        decode = versionData1(dataBin,dataToHex,serialCard)

    if version==0:
        decode = VersionData0(dataToHex,dataToIntList,dataToHexList,serialCard)

    return decode


serialObject=lib.getSerialObject()
login=lib.loginSector(serialObject,b'\x00',b'\xAA',lib.hexToBytes("B0B1B2B3B4B5")) #852D76D7634E Azul, B0B1B2B3B4B5 Titan, C09B3755B261 Parking, AF808D85BD56 Parking

if login==True:
    block=1
    print("LECTURA")
    data=(lib.readDataBlock(serialObject,block))
    if data==None:
        print("Read Failed!")
    else:
        print(data)
        decode = decodificar()
        print(decode)
else:
    print("Login Failed!")