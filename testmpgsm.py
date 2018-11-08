"""
    Ф-ции для работы с ModBus
    Попробуем запихнуть в класс, с возможностью переноса алгоритма на СИ

from machine import UART
from machine import Pin as GPIO
uDevice = UART(2, baudrate=9600, rx=16, tx=17, timeout=3000)
en485pin = GPIO(5,GPIO.OUT)
buff = bytearray([0x01,0x03,0x20,0x01,0x00,0x01,0x0a,0xde])
buff = bytearray([0x01,0x03,0x20,0x01,0x00,0x01,0xde,0x0a])

i'ts work
buff = bytearray([0x01,0x03,0x20,0x00,0x00,0x04,0x4f,0xc9])

buff = bytearray([0x01,0x03,0x20,0x04,0x00,0x02,0x8e,0x0a])

uDevice.any()


en485pin.value(0)
uDevice.write(buff)
en485pin.value(1)
uDevice.any()
uDevice.read(uDevice.any())


//work
en485pin.value(1)
uDevice.write(buff)
en485pin.value(0)
uDevice.any()
uDevice.read(uDevice.any())


"""

class ModBus:
    def __init__(self):
        print("init ModBus")

    def writeReg(self,devID,addr,value):
        """
        :param devID:   ID ус-ва
        :param addr:    адресс регистра
        :param value:   значение регистра
        :return:
        """
        data_out = bytearray()
        data_out.extend(devID)
        data_out.extend(MODBUS_FUNC_WRITE_REG)
        data_out.extend(addr>>8)
        data_out.extend(addr)

    def _add_crc_to_bytearray_(self, buff):
        crc = calc_crc(buff)
        data_out.extend(crc >> 8)
        data_out.extend(crc)
        return buff

    def calc_crc(self,buff):
        i = 0
        crc = 0xffff
        while (i < len(buff)):
            crc = self.crc16(crc,buff[i])
            i = i+1
        buff = crc
        buff = buff>>8
        buff = buff|((crc<<8)&0xff00)
        return buff

    def crc16(self,crc,newByte):
        crc = crc^newByte
        #print(crc)
        #for i=0; i<8; ++i
        i = 0
        while(i < 8):
            if(crc&1):
                crc = (crc>>1)^0xA001
            else:
                crc = crc>>1
            i=i+1

        return crc
        pass

modbus = ModBus()
#0x510302040001
buff = bytearray([0x01,0x03,0x20,0x04,0x00,0x02])

print(modbus.calc_crc(buff))



