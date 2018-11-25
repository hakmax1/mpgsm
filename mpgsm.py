#
#   Галкин Максим 
#   
#
#   http://185.41.186.74:1880/web
#   cd ~/esp/mpgsm/
#   ampy --port COM10 put mpgsm.py
#   ampy --port COM10 put wavecom.py
#   ampy --port COM10 put main.py
#   ampy --port COM10 run mpgsm.py
#   import mpgsm
#   esptool.py --port COM3 flash_id


#
#
#   at+cusd=1,*111#,15
#   at+cusd=1,*161#,15


import usocket as socket
import gsm
import os
from machine import UART
from machine import Pin as GPIO
import struct
import ujson
import _thread
import time
#parsed = ujson.loads("""{"name":"John"}""")

#print("Hello, this is GSM module")
print(os.listdir())

#gsm.debug(True)
#gsm.start(tx=23, rx=22,apn='www.ab.kyivstar.net')
#gsm.connect()

#import machine
#u2=machine.UART(2, baudrate=9600, rx=16, tx=17, timeout=10)
#u2.write("Hello, World!\n")

#if(gsm.status())

#http://185.41.186.74:1880/data
#addr = socket.getaddrinfo('185.41.186.74', 1880)[0][-1]
#print(s.readline())

#import gsm
#gsm.status()

SEND_DATA_TO_SERVER = 10
READ_DATA_FROM_SERVER = 11

ERR_NONE = 0
ERR_READ_DATA_FROM_SERVER = 10
ERR_READ_DATA_FROM_SERVER = 11


MODBUS_FUNC_READ_REG        = 0x03
MODBUS_FUNC_WRITE_REG       = 0x06

MODBUS_REG_IN_VOLTAGE       = 0x2000
MODBUS_REG_OUT_VOLTAGE      = 0x2001
MODBUS_REG_IN_CURRENT       = 0x2002
MODBUS_REG_OUT_CURRENT      = 0x2003
MODBUS_REG_KPD              = 0x2004
MODBUS_REG_T                = 0x2005
MODBUS_REG_STATE            = 0x2006
MODBUS_REG_UST_M_VOLTAGE    = 0x2007
MODBUS_REG_UST_M_CURRENT    = 0x2008
MODBUS_REG_UST_D_VOLTAGE    = 0x2009
MODBUS_REG_UST_D_CURRENT    = 0x200A
MODBUS_REG_UPR              = 0x200B

MODBUS_REG_STATE_MODE_BIT               = 0x01
MODBUS_REG_STATE_OUT_ONOFF_BIT          = 0x02
MODBUS_REG_STATE_ALLERT_VOLT_BIT        = 0x04
MODBUS_REG_STATE_ALLERT_T_BIT           = 0x08

MODBUS_REG_UPR_RESTART_BIT              = 0x01
MODBUS_REG_UPR_ONOFF_BIT                = 0x01
MODBUS_REG_UPR_CALIBR_BIT               = 0x01
MODBUS_REG_UPR_DIAGN_BIT                = 0x01


from wavecom import wavecom



"""
    Ф-ции для работы с ModBus
    Попробуем запихнуть в класс, с возможностью переноса алгоритма на СИ
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
    #                                                                                                               fixed
    def _add_crc_to_bytearray_(self, buff):
        crc = self.calc_crc(buff)
        #print("crc")
        #print(crc)
        #data_out = bytearray()
        #data_out.extend(buff)
        #print(data_out)
        buff.extend(crc.to_bytes(2,'big'))
        #data_out.extend(crc >> 8)
        #print(buff)
        return buff

    def calc_crc(self,buff):
        i = 0
        crc = 0xffff
        while (i < len(buff)):
            crc = self.crc16(crc,buff[i])
            i = i+1
        buff = crc
        buff = buff >> 8
        buff = buff | ((crc << 8) & 0xff00)
        return buff

    def crc16(self,crc,newByte):
        crc = crc^newByte
        #for i=0; i<8; ++i

        i = 0
        while (i < 8):
            if (crc & 1):
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
            i = i + 1

        return crc

        """
        
        if(crc&1):
            crc = (crc>>1)^0xA001
        else:
            crc = crc>>1

        return crc
        """






class Device:
    def __init__(self):
        print("init uDevice")
        self.ID = "1"
        # Номера ус-в
        self.dict_devices = (1, 2, 3, 4, 5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31)
        #self.registrPhoneNumbers = "+380665168235"

        self.ConfigModule = {}
        # default config

        self.registrPhoneNumbers = ["+380688810836","+380665168235"]

        self.gsmAPN = 'internet'
        self.gsmsocket_ip = '185.41.186.74'
        self.gsmsocket_port = 2021



        self.isDataFromServer = False
        self.isDataToServer = False
        self.datafromserver = bytearray()
        self.datatoserver = bytearray(100)
        self.serversock = socket.socket()
        self.err_thr_read = ERR_NONE

        #Событие из внешнего процесса на подключение к GSM
        self.evConnectGsm = False

        self.uDevice = UART(2, baudrate=9600, rx=16, tx=17, timeout=1000)
        #self.uGSMModule =
        self.count_pol_sec = 0
        self.count_tuggle_pol_sec = 0
        self.en485pin = GPIO(5,GPIO.OUT)
        self.indStateWorkPin = GPIO(12,GPIO.OUT)    # Постоянно моргаем
        self.indStateGPRSPin = GPIO(14, GPIO.OUT)   # Горит когда в режиме GPRS
        self.indStateErrorPin = GPIO(26, GPIO.OUT)  # Моргает когда есть ошибки
        self.indStateModemPin = GPIO(27, GPIO.OUT)  # Горит когда есть связь с модемом
        self.indStateRezervPin = GPIO(25, GPIO.OUT) # Резервный

        self.indStateWorkPin.value(0)
        self.indStateGPRSPin.value(0)
        self.indStateErrorPin.value(0)
        self.indStateModemPin.value(0)
        self.indStateRezervPin.value(0)

        # Для Wavecom
        self.gsm = wavecom()
        self.gsm.cb_exec_server_data = self._analis_server_socket_buff_
        self._send_data_to_server_ = self.gsm.send_data_to_server

        print("Init configuration")

        #f = open('config.json', 'w')


        self.gsm.cmd_CREATE_TCP_CLIENT = {'cmd': 'AT+WIPCREATE=2,1,"%s",%d\r\n'%(self.gsmsocket_ip,self.gsmsocket_port), 'cmd_resp': 'OK',
                                      'time_out': 6000,
                                      'delay': 0, 'skip': 0}


        self.StartThrTimePolSec()

        self.modbus = ModBus()

        # Для SIM800
        # gsm.debug(True)
        # gsm.start(tx=23, rx=22, apn=self.gsmAPN)
        # gsm.sms_cb(self.smscb, 5)

        #gsm.connect()
        #self.serversock.settimeout(0.5)
        #self.serversock.connect(('185.41.186.74', 2020))

    def LoadConfig(self,fname):
        pass
    def SaveConfig(self,fname):
        pass
    def ConnectToGSM(self):
        """
        Connect via GSM to server socket
        :return: none
        """
        #self.gsm.connect()
        #self.serversock.settimeout(0.5)
        #self.serversock.connect(('185.41.186.74', 2020))
        #self.serversock.connect(('google.ru', 80))
    def DisconnectGSM(self):
        """
        Disconnect from server
        :return: None
        """
        pass
    """
        callback - ф-ция приема сообщений
        
        int(indexes[0]) номер сообщения
        msg[2]  номер телефона
        msg[6]  текст сообщеия
    """
    def smscb(self,indexes):
        print("indexes = ",indexes)
        if(indexes):
            msg = gsm.readSMS(int(indexes[0]), True)
            if(self._is_register_phone_(msg[2])):
            #if(msg[2].find(self.registrPhoneNumbers)>=0):
                print("Phone Ok")
                ret = self._sms_cmd_exec_(msg[6])
                gsm.sendSMS(msg[2], ret)
            else:
                print("Not register phone number - ",msg[2])
            #На всякий случай удаляем все смс
            gsm.atcmd('AT+CMGDA="DEL ALL"', printable=True)
            return
        print("Errore indexes in smscb")
        pass
    def _is_register_phone_(self,phone):
        for el in self.registrPhoneNumbers:
            if el == phone:
                return True
        return False
    # Обработка текста сообщения
    def _sms_cmd_exec_(self,msg):
        print(msg)
        dmsg = msg.split(" ")
        #print(dmsg.count())
        if(len(dmsg)>0):
            try:
                if (dmsg[0]=="APN"):
                    self.gsmAPN = dmsg[1]
                    return "APN OK"

                elif (dmsg[0]=="IP"):
                    self.gsmsocket_ip =dmsg[1]
                    self.gsmsocket_port = int(dmsg[2])
                    return "IP OK"
                elif (dmsg[0]=="START"):
                    self.evConnectGsm = True
                    print("STARTGSM OK")
                    return "STARTGSM OK"
                return "ERR CMD"
            except IndexError:
                return "PARAM NUMBER ERRORE"
            except ValueError:
                return "PARAM VALUE ERRORE"


        pass
    def MainThread(self):
        # основной цикл
        if self.isDataFromServer:
            # есть данные от сервера
            self._analis_server_socket_buff_(self.datafromserver)
            self.isDataFromServer = False
            if(self.idThrReciveSocket != None):
                _thread.notify(self.idThrReciveSocket,SEND_DATA_TO_SERVER)
            if(self.err_thr_read != ERR_NONE):
                self.err_thr_read == ERR_NONE
                _thread.notify(self.idThrReciveSocket, READ_DATA_FROM_SERVER)


        
        if self.evConnectGsm == True:
            # Пробуем подключиться
            self.evConnectGsm = False
            if(self.isConnect() == False):
                print("Probuem podkluchitsya")
                self.ConnectToGSM()

        #else:
            # Пробуем отключиться
        #   if (self.isConnect == True):
        #       self.DisconnectGSM()

    """
        Основная ф-ция для объекта
        
    """
    def MainWavecom(self):

        try:
            while(True):
                # основной цикл для wavecom
                err = self.gsm.connect_to_gprs()
                if (err == True):
                    # соеденились с gprs
                    self.indStateGPRSPin.value(1)
                    self.indStateModemPin.value(1)
                    data_server = {}
                    data_server["ID"] = self.ID
                    data_server["cmd"] = "READY"
                    self._send_data_to_server_(data_server)
                    gprs_t_count = 0
                    while (gprs_t_count < 60):
                        gprs_t_count = gprs_t_count + 1
                        self.gsm.proc_server_data()
                else:
                    # Необходимо сообщить об ошибке
                    # Возможно модем в режиме чтения данных, проверим это
                    self.gsm.disconnect_gprs()
                    err = self.gsm.send_at_req(self.gsm.cmd_AT)
                    if(err != True):
                        # Ошибка связи с модемом
                        self.indStateErrorPin.value(1)
                        self.indStateModemPin.value(0)
                        self.indStateGPRSPin.value(0)
                    else:
                        self.indStateErrorPin.value(0)
                        self.indStateGPRSPin.value(0)
                        self.indStateModemPin.value(1)

                        # Пробуем еще раз
                        """
                        err = self.gsm.connect_to_gprs()
                        # соеденились с gprs
                        self.indStateGPRSPin.value(1)
                        self.indStateModemPin.value(1)
                        gprs_t_count = 0
                        while (gprs_t_count < 20):
                            gprs_t_count = gprs_t_count + 1
                            self.gsm.proc_server_data()
                        """
                err = self.gsm.disconnect_gprs()
                self.indStateGPRSPin.value(0)

                gprs_t_count = 0
                while (gprs_t_count < 5):
                    gprs_t_count = gprs_t_count + 1
                    #self.gsm.proc_at_data()

        except KeyboardInterrupt as e:
            print("MainWavecom except KeyboardInterrupt")
            self.StopThrTimePolSec()

        except Exception as e:

            print("MainWavecom except Exception")
            print(e)
            sys.print_exception(e)
            self.StopThrTimePolSec()


    def isConnect(self):
        state_int, state_str = gsm.status()
        if(state_int == 1):
            return True
        else:
            return False


    def writeCmd(self):
        self.uDevice.write("Hello")
        
    def __del__(self):
        print("del uDevice")
        self.uDevice.deinit()

    """
        Получить все данные от усв-ва                                                                               fixed
    """
    def GetDevData(self, dev):
        """
        Get all data from device
        :param dev: id(num) device, type integer
        :return: register value from device as type 'dict', or ['msg':'Error'] if not read data
        """
        self.uDevice.flush()
        finddev=False
        for devid in self.dict_devices:
            if(devid == dev):
                finddev = True
        if(finddev!=True):
            ret = {}
            ret["msg"] = "ERROR DEV_ID NOT PRESENT"
            return ret

        data_out = bytearray()
        data_out.extend(struct.pack('b', dev))
        data_out.extend(b'\x03\x20\x00\x00\x0C')
        self.modbus._add_crc_to_bytearray_(data_out)

        count_repeat = 3
        self._send_req_(data_out)
        while(count_repeat !=0):
            data = self._read_ans_()
            if (len(data) > 25):
                ret = self._alldata_modbus_to_strct_(data)
                if(ret.get("msg").get("devID") == dev):
                    return ret
                #print("Not eqal devID = ", ret.get("msg").get("devID"))
                count_repeat = count_repeat - 1
            else:
                count_repeat = count_repeat - 1
            print("repeat _send_req_, count = ",count_repeat)
            self._send_req_(data_out)
        #data = self._read_ans_()
        #print("data = ", data)
        #print("len(data) = ", len(data))
        #if(len(data)>25):
        #    ret = self._alldata_modbus_to_strct_(data)
        if (len(data) == 0):
            ret= {}
            ret["msg"]="Error"
        #data = data_out
        return ret

    def SetCtrlData(self, cmd_dict):
        """

        :param cmd_dict: {"devID":1,"reg":"01"}
        :return:
        """
        print("cmd_dict = ", cmd_dict)
        print("type cmd_dict = ", type(cmd_dict))
        self.uDevice.flush()
        data_out = bytearray()
        data_out.extend(struct.pack('b', cmd_dict.get("devID")))
        data_out.extend(b'\x06')
        data_out.extend(b'\x20\x0b')
        data_out.extend(struct.pack('>H', cmd_dict.get("reg")))
        self.modbus._add_crc_to_bytearray_(data_out)
        self._send_req_(data_out)
        return cmd_dict


    def SetDevData(self,cmd_dict):
        """
        From server comes a command like {"Iust":[0.15],"Uust":[0.25],"reg":"01"}

        :param cmd_dict:    dict param
        :return: register value from device as type 'dict', or
        """
        print("cmd_dict = ",cmd_dict)
        print("type cmd_dict = ", type(cmd_dict))
        self.uDevice.flush()


        #if(cmd_dict.get("cmd")==None):
        #    return "Error"

        Iust=cmd_dict.get("Iust")
        Uust = cmd_dict.get("Uust")
        reg = cmd_dict.get("reg")
        #float(str(data_dev_iust)[1:-1])
        print("Iust SetDevData")
        print(cmd_dict.get("Iust"))
        print("Uust SetDevData")
        print(cmd_dict.get("Uust"))
        print("reg SetDevData")
        print(cmd_dict.get("reg"))
        if (Iust != None):
            #print("Iust = ",Iust)
            Iust = float(str(Iust)[1:-1])
            Iust = Iust*100
            Iust = int(Iust)
            #print("Iusti = ", Iust)
            data_out = bytearray()
            data_out.extend(struct.pack('b', cmd_dict.get("devID")))
            data_out.extend(b'\x06')
            data_out.extend(b'\x20\x0A')
            data_out.extend(struct.pack('>H', Iust))
            self.modbus._add_crc_to_bytearray_(data_out)
            self._send_req_(data_out)
            data = self._read_ans_()
            print("data _read_ans_ = Iust ", data)

        if (Uust != None):
            Uust = float(str(Uust)[1:-1])
            Uust = Uust * 100
            Uust = int(Uust)
            # print("Iusti = ", Iust)
            data_out = bytearray()
            data_out.extend(struct.pack('b', cmd_dict.get("devID")))
            data_out.extend(b'\x06')
            data_out.extend(b'\x20\x09')
            data_out.extend(struct.pack('>H', Uust))
            self.modbus._add_crc_to_bytearray_(data_out)
            self._send_req_(data_out)
            data = self._read_ans_()
            print("data _read_ans_ Uust = ", data)

        if (reg != None):
            self.uDevice.flush()
            data_out = bytearray()
            data_out.extend(struct.pack('b', cmd_dict.get("devID")))
            data_out.extend(b'\x06')
            data_out.extend(b'\x20\x0b')
            data_out.extend(struct.pack('>H', cmd_dict.get("reg")))
            self.modbus._add_crc_to_bytearray_(data_out)
            self._send_req_(data_out)
            data = self._read_ans_()
            print("data _read_ans_ reg = ", data)


    def GetAllData(self):
        for dev in self.dict_devices:
            ans = self.GetDevData(dev)
            self._send_data_to_server_(ans)
            # self.serversock.send(ans)


    def _alldata_modbus_to_strct_(self, buff):
        """
        Analis buffer from device, on request get all registers
        buff - not  error
        :param buff:    input buffer
        :return:
                data from device in type 'dict'
        """
        try:
            # buff = bytearray([6, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ,5 ,5,6,7,7])
            # print("_alldata_modbus_to_strct_ buff len", len(buff))
            # print("_alldata_modbus_to_strct_ buff",buff[3],buff[4],buff[5],buff[6],buff[7],buff[8])

            data_device = {}
            data_device["devID"] = buff[0]
            data_u_in = struct.unpack('>H', buff[3:5])[0]
            data_u_in = data_u_in /100
            data_u_out = struct.unpack('>H', buff[5:7])[0]
            data_u_out = data_u_out /100
            data_i_in = struct.unpack('>H', buff[7:9])[0]
            data_i_in = data_i_in/100
            data_i_out = struct.unpack('>H', buff[9:11])[0]
            data_i_out = data_i_out / 100
            data_kpd = struct.unpack('>H', buff[11:13])[0]
            data_kpd = data_kpd / 100
            data_temper = struct.unpack('>H', buff[13:15])[0]
            data_temper = data_temper / 100
            data_reg_state = struct.unpack('>H', buff[15:17])[0]
            data_u_ust_local = struct.unpack('>H', buff[17:19])[0]
            data_u_ust_local = data_u_ust_local / 100
            data_i_ust_local = struct.unpack('>H', buff[19:21])[0]
            data_i_ust_local = data_i_ust_local / 100
            data_u_ust_dist = struct.unpack('>H', buff[21:23])[0]
            data_u_ust_dist = data_u_ust_dist / 100
            data_i_ust_dist = struct.unpack('>H', buff[23:25])[0]
            data_i_ust_dist = data_i_ust_dist / 100
            data_reg_upr = struct.unpack('>H', buff[25:27])[0]

            data_device["Uinput"] = data_u_in
            data_device["Uoutput"] = data_u_out
            data_device["Iinput"] = data_i_in
            data_device["Ioutput"] = data_i_out
            data_device["kpd"] = data_kpd
            data_device["temp"] = data_temper
            data_device["state"] = data_reg_state
            data_device["Udist"] = data_u_ust_local
            data_device["Idist"] = data_i_ust_local
            data_device["Ulocal"] = data_u_ust_dist
            data_device["Ilocal"] = data_i_ust_dist
            data_device["regupr"] = data_reg_upr

            data_to_server = {}
            data_to_server["msg"] = data_device
            data_to_server["timestamp"] = "10:10:10"
            #print(data_to_server)

            return data_to_server
        except NameError as e:
            print(e)
        pass

    def _read_ans_(self):
        is_data_read = False
        num_byte = 0
        read_buff = bytearray()
        time.sleep(0.3)
        self.en485pin.value(1)
        time.sleep(0.01)
        self.en485pin.value(0)
        time.sleep(0.01)

        while (is_data_read != True):
            bts = self.uDevice.read(1)
            #print("bts = ",bts)
            if (len(bts) != 0):
                bt = bts[0]
                #bt = ~bt
                if(len(read_buff)==0):
                    if(bt!=0):
                        #print("type(bt) = ",type(bt))
                        #print("bt = ", bt)
                        read_buff.append(bt)
                        num_byte += 1
                else:
                    read_buff.append(bt)
                    num_byte += 1
            else:
                is_data_read = True
            # Проверяем переполнение буффера
            if(len(read_buff)>100):
                print("!!!!!!!!!!!!!!!!   Error Overflow modbus in buffer")
                print("read_buff = ",read_buff)
                read_buff = bytearray()
                self.uDevice.flush()
                return read_buff
        return read_buff
    #                                                                                                               fixed
    def _send_req_(self, req):
        # Включаем передатчик
        self.en485pin.value(1)
        self.uDevice.write(req)
        #print(self.uDevice.write(req))
        #print(self.uDevice.any())
        time.sleep(0.01)
        #self.uDevice.flush()
        self.en485pin.value(0)

        # Выключаем передатчик
        #   Ждем ответа, если ответ пришел отправляем данные на сервер,
        #   если ответа нет или повторяем или отправляем серверу ошибку
        pass

    # Анализ данных от сервера
    # На всякий случай прорверяем в каком виде данные строка или буфер
    def _analis_server_socket_buff_(self, buff):
        try:
            print("_analis_server_socket_buff_              start")
            print("_analis_server_socket_buff_              buff = ",buff)
            if (type(buff) != str):
                stroka = ''
                for b in buff:
                    stroka += chr(b)
            else:
                stroka = buff
            print("stroka = ",stroka)
            try:
                in_data = ujson.loads(stroka)
            except ValueError as e:
                print("-------except ValueError in _analis_server_socket_buff_")
                return
            if (in_data.get("ID")!=self.ID):
                return
            # in_data = str
            print("in_data = ", in_data)
            print("-----_analis_server_socket_buff_------")

            #self._send_data_to_server_(in_data)
            # Смотрим какая команда пришла
            if (in_data.get("cmd") == "GETALLDATA"):
                # пришла команда опроса всех ус-в
                # Survey all devices from the list self.dict_devices
                print("GETALLDATA")

                for dev in self.dict_devices:
                    data = self.GetDevData(dev)
                    print("data = ", data)
                    print("type data = ", type(data))
                    timestamp = in_data.get("timestamp")
                    # data_dev_id = int(in_data.get("cmd")[len("GETDATA"):])
                    #data_dev_id = int(in_data.get("id"))
                    # print("data_dev_id = ", data_dev_id)
                    #data = self.GetDevData(data_dev_id)
                    data_device = {}
                    data_device["ID"] = self.ID
                    data_device["msg"] = data["msg"]
                    data_device["cmd"] = "DATA"
                    data_device["timestamp"] = timestamp
                    #print("self.GetDevData(data_dev_id) = ", data)
                    # print("type(data) = ", type(data))
                    self._send_data_to_server_(data_device)

            if (in_data.get("cmd").find("GETDATA") == 0):
                # пришла команда опроса одного ус-ва
                # Survey device num "id" from the list self.dict_devices
                print("cmd=GETDATA")
                timestamp = in_data.get("timestamp")
                #data_dev_id = int(in_data.get("cmd")[len("GETDATA"):])
                data_dev_id = int(in_data.get("msg").get("devID"))
                #print("data_dev_id = ", data_dev_id)
                data = self.GetDevData(data_dev_id)
                data_device = {}
                data_device["ID"] = self.ID
                data_device["msg"] = data["msg"]
                data_device["cmd"] = "DATA"
                data_device["timestamp"] = timestamp

                print("self.GetDevData(data_dev_id) = ", data)
                #print("type(data) = ", type(data))

                self._send_data_to_server_(data_device)
                # self.serversock.send(data)

            if (in_data.get("cmd").find("SETCTRL") == 0):
                #print("SETCTRL to dev")
                data_dev_id = int(in_data.get("msg").get("devID"))
                timestamp = in_data.get("timestamp")
                print("SETCTRL to dev - ",data_dev_id)
                data = self.SetCtrlData(in_data.get("msg"))
                print("SETCTRL data - ", data)
                data_device = {}
                data_device["ID"] = self.ID
                data_device["msg"] = data
                data_device["cmd"] = "SETCTRL"
                data_device["timestamp"] = timestamp
                self._send_data_to_server_(data_device)

                pass

            if (in_data.get("cmd").find("SETDATA") == 0):
                # пришла команда опроса установки параметров
                print("SETDATA")
                #data_dev_id = int(in_data.get("cmd")[len("SETDATA"):])
                data_dev_id = int(in_data.get("msg").get("devID"))
                timestamp = in_data.get("timestamp")
                print("data_dev_id = ", data_dev_id)
                data_dev_reg = in_data.get("msg").get("reg")
                data_dev_iust = in_data.get("msg").get("Iust")
                data_dev_uust = in_data.get("msg").get("Uust")
                #print("data_dev_reg = ", data_dev_reg)
                #print("Iust = ", data_dev_iust)
                #print("Uust = ", data_dev_uust)
                #print(type(data_dev_iust))
                #print(type(data_dev_uust))
                #print(str(data_dev_iust)[1:-1])
                #print(str(data_dev_uust)[1:-1])

                data = self.SetDevData(in_data.get("msg"))

                data_device = {}
                data_device["ID"] = self.ID
                data_device["msg"] = in_data.get("msg")
                data_device["cmd"] = "SETDATA"
                data_device["timestamp"] = in_data.get("timestamp")
                self._send_data_to_server_(in_data)

                #data_dev_iust = float(str(data_dev_iust)[1:-1])
                #data_dev_uust = float(str(data_dev_uust)[1:-1])

                #data_out = bytearray()

                #if(data_dev_id != None):
                #    data_out.extend(struct.pack('b', data_dev_id))
                #if (data_dev_reg != None):
                #    data_out.extend(struct.pack('b', data_dev_reg))
                #if (data_dev_iust != None):
                #    data_out.extend(struct.pack('f', data_dev_iust))
                #if (data_dev_uust != None):
                #    data_out.extend(struct.pack('f', data_dev_uust))

                #data_out.extend(b'\xaa')
                #print(data_out)
                # self._send_req_(data_out)
                # сформировали выходной буффер, можем отправлять
                #print("devID = ", data_dev_id)
                #print("reg = ", data_dev_reg)
                #print("Iust = ", data_dev_iust)
                #print("Uust = ", data_dev_uust)
                #print("data_out = ", data_out)

        except OSError as e:
            print("!!!!!!!!!!!!!!!  except OSError in _analis_server_socket_buff_   !!!!!!!!")
            print(e)
        except Exception as e:
            print("!!!!!!!!!!!!!!!  except Exception in _analis_server_socket_buff_   !!!!!!!!")
            data_device = {}
            data_device["ID"] = self.ID
            data_device["msg"] = in_data.get("msg")
            data_device["cmd"] = "ERROR TYPE"
            self._send_data_to_server_(data_device)
            print(e)
        finally:
            #print("!!!!!!!!!!!!!!!  except finally in _analis_server_socket_buff_   !!!!!!!!")
            pass
        # Анализируем входной буффер сервер соккета
        pass

    #   OK
    def _read_buff_to_json_(self, buff):
        # преобразуем даные от ус-ва в json объект
        try:
            # buff = bytearray([6, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ,5 ,5,6,7,7])
            data_device = {}
            data_device["devID"] = buff[0]
            data_u_in = struct.unpack('f', buff[1:5])
            data_u_out = struct.unpack('f', buff[5:9])
            data_i_in = struct.unpack('f', buff[9:13])
            data_i_out = struct.unpack('f', buff[13:17])
            data_t = struct.unpack('f', buff[17:21])

            data_device["Uinput"] = data_u_in
            data_device["Uoutput"] = data_u_out
            data_device["Iinput"] = data_i_in
            data_device["Ioutput"] = data_i_out
            data_device["temp"] = data_t
            data_device["temp"] = data_t

            data_to_server = {}
            data_to_server["msg"] = data_device
            data_to_server["timestamp"] = "10:10:10"

            return data_to_server
        except NameError as e:
            print(e)

    # Процесс индикации работы ус-ва
    def IndProc(self):
        self.count_pol_sec+=1
        if(self.count_tuggle_pol_sec == 0):
            self.count_tuggle_pol_sec = 1
            self.indStateWorkPin.value(1)
            #self.indStateModemPin.value(1)
        else:
            self.count_tuggle_pol_sec = 0
            self.indStateWorkPin.value(0)
            #self.indStateModemPin.value(0)
        pass

    #   Запуск потока таймера 0,5 сек
    def StartThrTimePolSec(self):
        self.idThrTimePolSec = _thread.start_new_thread("ThrTimePolSec", self.ThrTimePolSec, ())
    #   Остановка потока таймера 0,5 сек
    def StopThrTimePolSec(self):
        if (self.idThrTimePolSec != None):
            _thread.stop(self.idThrTimePolSec)
    def ThrTimePolSec(self):
        # Поток для вызова ф-ций каждые пол секунды
        i = 0
        try:
            while i < 100:
                self.IndProc()
                notification = _thread.wait(500)
                if (notification == _thread.EXIT):
                    print("ThrTimePolSec.EXIT")
                    break
        except KeyboardInterrupt:
            print("ThrTimePolSec KeyboardInterrupt")
        except Exception:
            print("ThrTimePolSec Exception")

    # ==================================================================================================================
    # ==================================================================================================================
    #               Функции для модема SIM800
    # ==================================================================================================================
    # ==================================================================================================================
    def set_call_state_gsm(self):
        gsm.stop()
        time.sleep(4)
        #self.uDevice = UART(2, baudrate=9600, rx=16, tx=17, timeout=3000)
        self.gsm_call = UART(1, baudrate=115200, rx=22, tx=23, timeout=3000,buffer_size=100)
        self.gsm_call.flush()
        #self.gsm_call.callback(uart.CBTYPE_DATA, self.gsm_call_cb, data_len=12)
        self.gsm_call.callback(gsm_call.CBTYPE_PATTERN, gsm_call_cb, pattern=b'\r\n')
    def gsm_call_cb(self,res):
        print("[UART CB]", res[2])
        if(res[2]=='RING'):
            #запросс номера
            print("Day nomer")
            gsm_call.write('AT+CLCC\r\n')
            pass
        #gsm.start(tx=23, rx=22, apn=self.gsmAPN)
    #   Запуск потока чтения из соккета
    def StartThrReciveSocket(self):
        self.idThrReciveSocket = _thread.start_new_thread("ThrReciveSocket", self.ThrReciveSocket, ())
    #   Остановка потока чтения из соккета
    def StopThrReciveSocket(self):
        if (self.idThrReciveSocket != None):
            _thread.stop(self.idThrReciveSocket)
    def ThrReciveSocket(self):
        print("thrReciveSocket is RUN")
        #_thread.allowsuspend(True)
        # while True:
        i = 0
        while i < 100:
            i = i + 1
            print("Hello from thread")
            print(_thread.getSelfName())
            # mainID = _thread.getReplID()
            # print(mainID)
            # print(_thread.getmsg())

            if (self.isConnect()):
                # если есть соеденение то читаем из соккета
                isOk = False
                cntByte = 0
                self.datafromserver = bytearray()
                while(isOk!=True):
                    try:
                        bn = self.serversock.read(1)
                        self.datafromserver.extend(chr(bn[0]))
                        cntByte+=1
                    except OSError as e:
                        if e.args[0] == 110:
                            if cntByte>0:
                                isOk = True
                        #print(e)
                        #print("cntByte = ", cntByte)
                self.isDataFromServer = True
                print("read data size = ", cntByte)
                print("len data size = ", len(self.datafromserver))
                print(self.datafromserver)
                """
                try:
                    print("self.isConnect()")
                    bn = self.serversock.readinto(self.datafromserver)
                    if(bn >0):
                        self.isDataFromServer = True
                    else:
                        self.err_thr_read = ERR_READ_DATA_FROM_SERVER
                    print("read data size = ",bn)
                    print("len data size = ", len(self.datafromserver))
                    print(self.datafromserver)
                except OSError as e:
                    print("!!!!!!!! except OSError in ThrReciveSocket")
                    # выставляем флаг того что была ошибка
                """
            notification = _thread.wait()
            print("notification = " ,notification)
            if (notification == _thread.EXIT):
                print("_thread.EXIT")
                break
            #if (notification == 10):
                #print("SEND_DATA_TO_SERBER == 1")
                #if (self.isConnect()):
                #    try:
                #        self.serversock.send(self.datatoserver)
                #    except OSError as e:
                #        print("!!!!!!!! except OSError in ThrReciveSocket")
                # выставляем флаг того что была ошибка
                #continue

        print("Stop thrReciveSocket")

device = Device()




#in_buff = bytearray([6, 0, 0,128, 0, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5 ,5 ,5,6,7,7])
#data_server = '{"cmd":"SETDATA0","msg": {"reg": 6, "Iust": [1.5e-1], "Uust": [2.5e-1]}, "timestamp": "10:10:10"}'
#data_to_server = device._read_buff_to_json_(in_buff)
#print("------------------------------------------------")
#print(data_to_server)
#print("------------------------------------------------")
#print(ujson.dumps(data_to_server))
#print("------------------------------------------------")


#print("------------------------------------------------")

#print("------------------------------------------------")
#print("------------------------------------------------")




#device.StartThrReciveSocket()
#k = 0

#while True:
#    device.MainThread()
    #print(_thread.list())
#    time.sleep(2)
    #print(k)
#    k+=2
    #device.StopThrReciveSocket()
    #print(_thread.list())
#device.StopThrReciveSocket()
#gsm.stop()
    
#   Запросс данных конткретного ус-ва
#   Послали запросс и ждем ответа
#   Если превышено время ожидания, пробуем повторить    
def GetData(nDev,timeout):
    #   После того как пришли данные, упаковываем их в удобный формат
    
    #чтение данных, чтение всех данных, и если их нет возвращает None
    #data = uDevice.read()
    pass

#   Запросс данных конткретного ус-ва
def SetData(nDev):
    # 1 байт - Адресс ус-ва
    # 2 байт - Регистр дискретных уставок
    # 3-6 байт - Уставка тока
    # 7-10 байт - Уставка напряжения
    # 11 байт - CRC 
    # 1 байт - Адресс ус-ва
    # 1 байт - Адресс ус-ва
    
    pass

#   Отправить запрсс ус-ву, и ожидать ответа.
#   Скорее всего сделать это в отдельном потоке
def ReqAns(cmd, timeout):
    pass

def SendDataToServer():
    pass

    
    








