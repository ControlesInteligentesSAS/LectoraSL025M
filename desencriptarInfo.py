import SL025MPy3 as lib
from datetime import datetime

def byteToHex(byte:bytes)->str:
    return ''.join(format(b, '02x') for b in byte)

def twos_complement(val,bits)->int:
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)       
    return val  

def getSerialCard(serial):
    selectC=lib.selectCard(serial)
    keySerial:str=selectC["uid"][6:8]+selectC["uid"][4:6]+selectC["uid"][2:4]+selectC["uid"][0:2] #Se invierte el patron de bits
    keyEnc=[int(selectC["uid"][0:2],16),int(selectC["uid"][2:4],16),int(selectC["uid"][4:6],16),int(selectC["uid"][6:8],16)]
    serialCard=int(keySerial,16)
    return serialCard,keyEnc

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

def readData(data:list,key):
    versionData=False

    rnd=[data[len(data)-1]>>3]

    keyEnc=[None]*4
    for i in range (0,len(key),1):
        keyEnc[i]=key[i]^rnd[i%len(rnd)]
    
    dataBinDeco=[]
    for x in range (0,len(data),1):
        dataBinDeco.append(data[x]^keyEnc[x % len(keyEnc)])
    version=data[len(data)-1] & 7
    dataBinDeco[len(dataBinDeco)-1]=version

    checksum = checkSumArray(dataBinDeco)

    if checksum:
        versionData = True
        return versionData,dataBinDeco
    else:
        return versionData,data

def VersionData0(dataHex:str, dataInt:list, dataHexList:list,serial:int,checksum:bool)->str:
    print("serialcard:", str(serial))
    print("Data:", dataHex.upper())
    for i in range (0,len(dataHexList),1):
        if len(dataHexList[i])==1:
            dataHexList[i]="0"+dataHexList[i]
    if checksum:
        time=dataHexList[3]+dataHexList[2]+dataHexList[1]+dataHexList[0]
    else:
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

def versionData1(data:list,dataHex:str,serial:int)->str:
    print("serialcard:", str(serial))
    print("Data:", dataHex.upper())
    dataToHexList=[]
    for k in data:
        dataToHexList.append(hex(k)[2:4])
    fecha2000=946702800 # Fecha de inicio en formato Epoch (2000/01/01 00:00:00 GMT-05:00)
    time=dataToHexList[3]+dataToHexList[2]+dataToHexList[1]+dataToHexList[0]
    time1=int(time,16)
    entrada=datetime.fromtimestamp(fecha2000+time1)
    convenios = str(data[4])+" "+str(data[5])+" "+str(data[6]) #REVISAR
    minToExit=str(int(hex(data[8])[2:]+hex(data[7])[2:],16))
    tipo=str(data[9]>>3)
    estado=str(data[9]&7)
    consola=str(data[10])
    park=str(data[11])
    varios=str(data[12])
    free=str(data[13])
    if estado=='1' or estado=='2':
        #Redim Preverse bytesSerPagoConvenios (convenios)
        #fechaPagoSalida= fechaEntrada.AddSeconds(BitConverter.ToUInt32(bytesSerPagoConvenios, 0))
        fechaPagoSalida= ""
        if estado=='1':
            return ("Entrada: {} Pagó: {} Min To Exit: {} Tipo: {} Estado: {} Consola: {} Park: {} Varios: {} Free: {}".format(entrada,fechaPagoSalida,minToExit,tipo,estado,consola,park,varios,free))    
        else:
            return ("Entrada: {} Salida: {} Min To Exit: {} Tipo: {} Estado: {} Consola: {} Park: {} Varios: {} Free: {}".format(entrada,fechaPagoSalida,minToExit,tipo,estado,consola,park,varios,free))    
    else:
        return ("Entrada: {} Convenios: {} Min To Exit: {} Tipo: {} Estado: {} Consola: {} Park: {} Varios: {} Free: {}".format(entrada,convenios,minToExit,tipo,estado,consola,park,varios,free))

def decodificar(serialObject,data)->str:
    version=0
    dataToHex,dataToIntList,dataToHexList = conversiones(data)
    serialCard,keyEnc = getSerialCard(serialObject)
    checksum,dataBin=readData(dataToIntList,keyEnc)
    dataToHexList=[] #Lista en formato Hex de la data
    for k in dataBin:
        dataToHexList.append(hex(k)[2:4])
    decode = ""
    print("DECODE")
    if checksum:
        version=dataBin[len(dataBin)-1]

    if version==1:
        print("VERSION 1")
        decode = versionData1(dataBin,dataToHex,serialCard)
    else:
        print("VERSION 0")
        decode = VersionData0(dataToHex,dataBin,dataToHexList,serialCard,checksum)

    return decode

def readDatos():
    serialObject=lib.getSerialObject()
    login=lib.loginSector(serialObject,b'\x00',b'\xAA',lib.hexToBytes("C09B3755B261")) #852D76D7634E Azul, B0B1B2B3B4B5 Titan, C09B3755B261 Parking, AF808D85BD56 Parking

def readDataDecoded(serialObject,login):
    if login==True:
        block=1
        print("LECTURA")
        data=(lib.readDataBlock(serialObject,block))
        if data==None:
            print("Read Failed!")
        else:
            print(data)
            decode = decodificar(serialObject,data)
            print(decode)
    else:
        print("Login Failed!")

#serial,login=readDatos()
#readDataDecoded(serial,login)