# LectoraSL025M
Librería en Python para manejar la lectora SL025M

Esta librería permite configurar y hacer uso de la Lectora SL025M para escribir y leer datos en tarjetas

## Modo de comunicación:
 
La lectora SL025M se comunica a través del puerto serial al Host pudiendo enviar y recibir información por el puerto al que se conecta.

Requerimientos:
```sh
Python 3.x
```

## Instalación:
Descargar el repositorio en https://github.com/ControlesInteligentesSAS/LectoraSL025M
Instalar dependencias:
```sh
pip install pyserial
```
Copiar el script SL025MPy3.py en la carpeta de su proyecto
Para importar la librería se usa: 
```sh
import SL025MPy3
```

## Uso:

La librería provee varias funciones para lograr la comunicación mediante serial y para leer y escribir información en tarjetas, las cuales se podrán usar de acuerdo a la acción que se desea realizar. 

## Tipos de estados:
Cuando se ejecuta una función, la lectora puede responder con los siguientes estados:
- Success
- No tag
- Login Succeed
- Login Fail
- Read Fail
- Write Fail
- Unable to read after write
- Address overflow
- Download key fail
- No authenticate
- Not a value block
- Invaled len of command format
- Checksum error
- Command code error

## Funciones

### getSerialObject:
Devuelve un objeto serial que tiene conexión con la lectora. El objeto serial se usará para enviar los comandos a la lectora incluidos en las demás funciones.

**Ejemplo de uso:**
```sh
serialObject=getSerialObject()
```

**Ejemplo de respuesta:**
```sh
Serial<id=0xffffa7929b50, open=True>(port='/dev/ttyReader', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
```

### selectCard:
Devuelve el ID y el tipo de tarjeta que se encuentra sobre la lectora. La función espera como argumento el puerto serial a donde está conectada la lectora.

**Ejemplo de uso:**
```sh
selectCard(serialObject)
```

**Ejemplo de respuesta exitosa:**
```sh
UID: b'\x24\xb5\x05\xc5'
UID in Decimal: 615843269
Type: Mifare 4k, 4 byte UID
```
**Ejemplo de respuesta errónea:**
```sh
Response status: No tag
Error: No tag
None
```

### loginSector:
Inicia sesión en un sector de la tarjeta. La función retorna True si el inicio de sesión fue exitosa, de lo contrario retornará False
Nota: El inicio de sesión es indispensable para el uso de las funciones que se nombran en seguida.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora  
- sector (bytes): Sector en donde se iniciará sesión 0X00 - 0x27
- keyType (bytes): Tipo de llave a usar (0xAA, 0xBB)
- key (bytes): Llave con la que se iniciará sesión, 6 bytes

**Ejemplo de uso:**
```sh
loginSector(serialObject,b'\x01',b'\xAA',b'\xb0\xb1\xb2\xb3\xb4\xb5')
```
También se puede usar la función hexToBytes si se tiene la llave en formato hexadecimal
```sh
loginSector(serialObject,b'\x01',b'\xAA',hexToBytes("B0B1B2B3B4B5"))
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
True
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Login fail
Error login falied! Login fail
False
```

### downloadKeyIntoReader:
Permite descargar la llave directamente en la lectora. La función retorna True si la llave fue descargada, de lo contrario retornará False.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora  
- sector (bytes): Sector en donde se iniciará sesión 0X00 - 0x27
- keyType (bytes): Tipo de llave a usar (0xAA, 0xBB)
- key (bytes): Llave con la que se iniciará sesión, 6 bytes

**Ejemplo de uso:**
```sh
downloadKeyIntoReader(serialObject,b'\x00',b'\xAA',b'\xb0\xb1\xb2\xb3\xb4\xb5')
```
También se puede usar la función hexToBytes si se tiene la llave en formato hexadecimal
```sh
downloadKeyIntoReader(serialObject,b'\x00',b'\xAA',hexToBytes("852D76D7634E")
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
True
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Download fail
Download failed! Download fail
False
```


### loginStoredKey:
Inicia sesión en un sector de la tarjeta con la llave previamente descargada con la función downloadKeyIntoReader. Esta función es una alternativa a la función loginSector. La función retorna True si el inicio de sesión fue exitosa, de lo contrario retornará False

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora  
- sector (bytes): Sector en donde se iniciará sesión 0X00 - 0x27
- keyType (bytes): Tipo de llave a usar (0xAA, 0xBB)

**Ejemplo de uso:**
```sh
loginSectorStoredKey(serialObject,b'\x00',b'\xAA')
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
True
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Login fail
Login failed! Login fail
False
```


### readDataBlock:
Lee un bloque de datos de la tarjeta. La función retorna la data leída

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- bloque (int): Dirección del bloque que se va a leer

**Ejemplo de uso:**
```sh
readDataBlock(serialObject,0)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\xb1\x03\x01\xa0\xff\x00\x07\x02\x04\n\xb2\x01\x01\x08\x07\x07'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Not authenticate
Read data block failed! Not authenticate
None
```


### writeDataBlock:
Permite escribir en un bloque de datos de la tarjeta. La función retornará el bloque de datos escrito si la operación es exitosa.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- bloque (int): Dirección del bloque que se va a leer
- data (list): Los datos que se van a escribir, el tamaño de la lista debe ser de 16

**Ejemplo de uso:**
```sh
data=[146, 9, 250, 113, 19, 7, 0, 1, 0, 0, 0, 0, 2, 1, 0, 171]
writeDataBlock(serialObject,1,data)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\xb1\x03\x01\xa0\x0f\x00\x0a\x02\x04\n\xb2\x01\x02\x08\x00\x04'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Not authenticate
Write data block failed! Not authenticate
None
```

### readValueBlock:
Lee el valor de un bloque. La función retorna el valor del bloque si la operación es exitosa

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- bloque (int): Dirección del bloque que se va a leer

**Ejemplo de uso:**
```sh
readValueBlock(serialObject,2)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\xb2\x00\x01\xa0'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Not a value block
Read value block failed! Not a value block
None
```


### inicializeValueBlock:
Escribe el valor de un bloque. La función retorna el valor de un bloque si la operación es exitosa.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- bloque (int): Dirección del bloque que se va a leer
- value (list): El valor de escribir, el tamaño de la lista debe ser de 4

**Ejemplo de uso:**
```sh
value=[32,54,67,5]
inicializeValueblock(serialObject,1,value)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\xb2\x00\x04\x0f'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Unable to read after write
Read value block failed! Unable to read after write
None
```


### writeMasterKey:
Escribe la llave maestra en la tarjeta. La función retorna la llave de autenticación escrita si la operación fue exitosa.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- sector (bytes): Sector donde se escribirá la llave 0X00 - 0x27
- key (bytes): Llave de autenticación a escribir

**Ejemplo de uso:**
```sh
writeMasterKey(serialObject,b'\x00',hexToBytes("C09B3755B261"))
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\x08\xb1\x06\x1f\x1e\0e'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Write fail
Write master key failed! Write fail
None
```

### incrementValue:
Incrementa el valor del bloque. La función retorna el valor después del incremento si la operación fue exitosa.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- block (int): Dirección del bloque que se va a incrementar
- value (list): El valor a ser incrementado

**Ejemplo de uso:**
```sh
value=[32,54,67,5]
incrementValue(serialObject,1,value)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\x08\xb1\x06\x0f'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Not a value block
Increment value failed! Not a value block
None
```


### decrementeValue:
Decrementa el valor del bloque. La función retorna el valor después del decremento si la operación fue exitosa.

**Argumentos:**
serial (serial): Puerto serial donde está conectada la lectora
block (int): Dirección del bloque que se va a decrementar
value (list): El valor a ser decrementado

**Ejemplo de uso:**
```sh
value=[32,54,67,5]
decrementValue(serialObject,1,value)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\x04\x03\x02\x1f'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Not a value block
Decrement value failed! Not a value block
None
```


### copyValue:
Copia el valor de un bloque en otro bloque. la función retorna el valor después de copiar si la operación es exitosa.

**Argumentos:**
serial (serial): Puerto serial donde está conectada la lectora
fuente (int): El bloque desde donde se va a copiar el valor
destino (int): El bloque destino a donde se copiará el valor
La fuente y el destino deben estar en el mismo sector

**Ejemplo de uso:**
```sh
copyValue(serialObject,0,1)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\x08\xb1\x03\x1f'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Not authenticate
Copy value failed! Not authenticate
None
```


### readDataPage:
Lee una página de datos (UltraLight & NTAG203). La función retorna el bloque de datos si la operación es exitosa.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- page (int): El número de página a leer, 0x00 - 0x0F

**Ejemplo de uso:**
```sh
readDataPage(serialObject,1)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\x01\n\x0b\n'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Read fail
Read data page failed! Read fail
None
```

### writeDataPage:
Escribe una página de datos (UltraLight & NTAG203). La función retorna el bloque de datos si la operación es exitosa.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- page (int): El número de página a escribir, 0x00 - 0x0F
- data (list): Los datos a escribir, el tamaño de la lista debe ser de 4

**Ejemplo de uso:**
```sh
data=[4,3,2,5]
writeDataPage(serialObject,1,data)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'\x01\n\x05\0c'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Unable to read after write
Write data page failed! Unable to read after write
None
```

### manageRedLed:
Para el manejo del led rojo. La función retorna True si la operación es exitosa, de lo contrario retorna False.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora
- code (int): 0 para led apagado, 1 para led encendido

**Ejemplo de uso:**
```sh
manageRedLed(serialObject,b'\x01')
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
True
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Checksum error
Manage red led failed! Checksum error
False
```
### getFirmwareVersion:
Retorna la versión del firmware de la lectora.

**Argumentos:**
- serial (serial): Puerto serial donde está conectada la lectora

**Ejemplo de uso:**
```sh
getFirmwareVersion(serialObject)
```
**Ejemplo de respuesta exitosa:**
```sh
Response status: Success
b'xbd\x0c\xf0\x00SL025-1.8c'
b'SL025-1.8c'
```

**Ejemplo de respuesta errónea:**
```sh
Response status: Checksum error
Get firmware version failed! Checksum error
```
