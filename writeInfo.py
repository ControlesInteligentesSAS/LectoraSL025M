import SL025MPy3 as lib
from datetime import datetime, date

def checksumArray(data:list)->int:
    checksum=0
    for i in range(0,len(data)-2,1):
        checksum=checksum^data[i]
    return checksum

def encryptArray(data:list,key:list,version:int):
    rnd=[data[len(data)-1]>>3]
    output=[None]*16
    keyEnc=encryptKey(key,rnd)
    for i in range(0,len(data),1):
        output[i]=data[i] ^ keyEnc[i%len(key)]
    output[len(output)-1]=(rnd[0]<<3)+(version&7)
    return output

def encryptKey(data:list,key:list)->list:
    output=[None]*4
    for i in range(0,len(data),1):
        output[i]=data[i]^key[i%len(key)]
    return output

def versionData0(dataEnv:list)->list:
    versionData=0
    IntList=[]
    dateToHex=hex(int(dataEnv[0]))[2:].upper()
    hexListDate=[dateToHex[6:8],dateToHex[4:6],dateToHex[2:4],dateToHex[0:2]]
    for k in hexListDate:
        IntList.append(int(k,16))

    IntList.extend([dataEnv[1],dataEnv[7],dataEnv[9],dataEnv[2],dataEnv[3],dataEnv[4],dataEnv[5],dataEnv[6],dataEnv[8],dataEnv[11],dataEnv[12],dataEnv[10]])
    return IntList

def versionData1(dataEnv:list)->list:
    IntList=[]
    segEntradaList=[]
    now = datetime.now()
    fechaPago_o_Convenios=[None]*3
    nowSalida=datetime.now()
    fechaInicio=946702800 # Fecha de inicio en formato Epoch (2000/01/01 00:00:00 GMT-05:00)
    byteCardTypeAndEstado=(dataEnv[6]<<3)+(dataEnv[2] & 7)
    minToExit2=0
    if dataEnv[10]>255:
        minHex=hex(dataEnv[10])[2:]
        if len(minHex) % 2==1:
            minHex="0"+minHex
        dataEnv[10]=int(minHex[2:4],16)
        minToExit2=int(minHex[0:2],16)

    fechaSalida=nowSalida.strftime("%Y%m%d%H%M")[2:] #Fecha de salida
    segEntrada=int(datetime.timestamp(now))-fechaInicio
    segEntradaHex=hex(segEntrada)[2:]
    segEntradaList=[segEntradaHex[6:8],segEntradaHex[4:6],segEntradaHex[2:4],segEntradaHex[0:2]]
    if dataEnv[2]==0 or dataEnv[2]==3:
        fechaPago_o_Convenios[0]=dataEnv[3]
        fechaPago_o_Convenios[1]=dataEnv[4]
        fechaPago_o_Convenios[2]=dataEnv[5]
    elif dataEnv[2]==1 or dataEnv[2]==2:
        if dataEnv[0]>fechaSalida:
            print("Error, fecha de entrada mayor a la fecha de salida")
        else:
            segPagoSalida=int(datetime.timestamp(now))-int(datetime.timestamp(nowSalida))
            bytesSeconds=[segPagoSalida,0,0,0]
            fechaPago_o_Convenios.append(bytesSeconds[0])
            fechaPago_o_Convenios.append(bytesSeconds[1])
            fechaPago_o_Convenios.append(bytesSeconds[2])
    else:
        print("El byte de pago es erroneo")

    IntList.extend([int(segEntradaList[0],16),int(segEntradaList[1],16),int(segEntradaList[2],16),int(segEntradaList[3],16),fechaPago_o_Convenios[0],fechaPago_o_Convenios[1],fechaPago_o_Convenios[2],int(dataEnv[10]),minToExit2,byteCardTypeAndEstado,dataEnv[1],dataEnv[7],dataEnv[8],dataEnv[9],dataEnv[9],dataEnv[9]])
    return IntList

def writeData(versionData:int):
    serialObject=lib.getSerialObject()
    login=lib.loginSector(serialObject,b'\x00',b'\xAA',lib.hexToBytes("C09B3755B261")) #852D76D7634E Azul

    checked=False
    versionData=versionData

    if versionData==1:
        dataEnv=dataEnv1()
        dataToWrite=versionData1(dataEnv)
        #print(dataToWrite)
    else:
        dataEnv=dataEnv0()
        dataToWrite=versionData0(dataEnv)
        #print(dataToWrite)

    selectC=lib.selectCard(serialObject)
    serialBin=[int(selectC['uid'][0:2],16),int(selectC['uid'][2:4],16),int(selectC['uid'][4:6],16),int(selectC['uid'][6:8],16)]

    checksum=checksumArray(dataToWrite)
    dataToWrite[len(dataToWrite)-2]=checksum
    dataEnc=encryptArray(dataToWrite,serialBin,versionData)
    dataHex=[]
    for i in dataEnc:
        dataHex.append(hex(i)[2:])
    dataStr=""
    for i in range(0,len(dataHex),1):
        if len(dataHex[i])==1:
            dataHex[i]="0"+dataHex[i]
        dataStr=dataStr+dataHex[i]

    escritura=(lib.writeDataBlock(serialObject,1,dataEnc))
    print("ESCRITURA")
    print(escritura)
    print("Data Written", dataStr.upper())
    return serialObject,login

def dataEnv0()->list:
    now = datetime.now()
    fechaEntrada = now.strftime("%Y%m%d%H%M")[2:] #Fecha
    seconds = int(now.strftime("%S")) #Numero de segundos

    #Convenios
    c1=9
    c2=5
    c3=4
    c4=7
    c5=1

    idConsola=3 #Id de la consola
    bytePago=1 #Byte de pago  0-Entro, 1-Pago, 2-Salio, 3?
    byteCardType=0 #tipo de tarjeta   0-Normal, 1-VIP, 2-Mensual
    bytefinal=30
    idPark=4 #Id del parqueadero
    var1=0 #CONSTANTE QUE NO CAMBIA
    
    dataEnv=[fechaEntrada,seconds,c1,c2,c3,c4,c5,idConsola,bytePago,byteCardType,bytefinal,idPark,var1]
    return dataEnv

def dataEnv1()->list:
    now = datetime.now()
    fechaEntrada = now.strftime("%Y%m%d%H%M")[2:] #Fecha
    idConsola=9 #Id de la consola
    bytePago=0 #Byte de pago  0-Entro, 1-Pago, 2-Salio, 3?
    byteCardType=0 #tipo de tarjeta   0-Normal, 1-VIP, 2-Mensual
    idPark=7 #Id del parqueadero
    mintoExit=19 #Minutos para salir
    #convenios
    c1=8
    c2=9
    c3=0
    varios=5
    free=33 #free, checksum, versionData
    dataEnv=[fechaEntrada,idConsola,bytePago,c1,c2,c3,byteCardType,idPark,varios,free,mintoExit]
    return dataEnv

serial,login=writeData(0)
import desencriptarInfo as des
des.readDataDecoded(serial,login)