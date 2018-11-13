#
#   Галкин Максим
#
#
#
#   cd ~/esp/mpgsmgcv/mpgsm/
#   ampy --port COM8 put wavecom.py
#   ampy --port COM8 run mpgsm.py
#   import mpgsm
#   cmd_START_GPRS_BR НЕ ПРОХОДИТ
#
#   Переводим для СМС
#   AT+CSCS= "GSM"
#   AT+CMGF=0
#   AT+CMGF=1
#   +CMTI: "SM",4    пришло смс
#   AT+CMGL="ALL"
#   AT+CMGDA="DEL ALL"      ("DEL READ","DEL UNREAD","DEL SENT","DEL UNSENT")
#   AT+CMGDA="ALL"  AT+CMGDA="DEL READ" AT+CMGDA="READ"  AT+CMGD=1,4
#
#   The message is returned as tuple:

#        Position	Content	Note
#        0	idx	integer, message index
#        1	status	string: "REC UNREAD" or "REC READ"
#        2	from	string, sender's GSM number in international format
#        3	time	string, message time as string in GSM format
#        4	timeval	integer, message time as unix time
#        5	tz	integer, message time zone
#        6	msg	string, message text




import time
import _thread
from machine import UART
import ujson

#cmd_AT = {'cmd':"AT\r\n",'cmd_resp':'OK','time_out':1,'delay':0,'skip':0}

class wavecom:
    def __init__(self):

        print("init WaveCom Device")
        self._responce = ''
        self._f_read_data_from_server = False           # Флаг чтения данных с сервера
        self._f_resp_ok = False                         # Флаг успешного запросса
        self._f_device_ok = False                       # Флаг успешного подключения к модему

        self._f_err_no_connect_gprs = False
        self._f_err_no_connect_module = False

        self.cb_exec_server_data = None



        self.cmd_AT = {'cmd':"AT\r\n",'cmd_resp':'OK','time_out':1000,'delay':0,'skip':0}
        self.cmd_CONNECT = {'cmd': "AT\r\n", 'cmd_resp': 'OK', 'time_out': 1, 'delay': 0, 'skip': 0}
        self.cmd_START_IP_STACK = {'cmd': "AT+WIPCFG=1\r\n", 'cmd_resp': 'OK', 'time_out': 3000, 'delay': 0, 'skip': 0}
        self.cmd_STOP_IP_STACK = {'cmd': "AT+WIPCFG=0\r\n", 'cmd_resp': 'OK', 'time_out': 3000, 'delay': 0, 'skip': 0}
        self.cmd_OPEN_GPRS_BR = {'cmd': "AT+WIPBR=1,6\r\n", 'cmd_resp': 'OK', 'time_out': 3000, 'delay': 0, 'skip': 0}
        self.cmd_APN_GPRS_BR = {'cmd': 'AT+WIPBR=2,6,11,"internet"\r\n', 'cmd_resp': 'OK', 'time_out': 3000, 'delay': 0,
                           'skip': 0}
        self.cmd_START_GPRS_BR = {'cmd': 'AT+WIPBR=4,6,0\r\n', 'cmd_resp': 'OK', 'time_out': 6000, 'delay': 0, 'skip': 0}
        self.cmd_STOP_GPRS_BR = {'cmd': 'AT+WIPBR=5,6\r\n', 'cmd_resp': 'OKK', 'time_out': 6000, 'delay': 0, 'skip': 0}
        self.cmd_CLOSE_GPRS_BR = {'cmd': 'AT+WIPBR=0,6\r\n', 'cmd_resp': 'OKK', 'time_out': 6000, 'delay': 0, 'skip': 0}
        self.cmd_CREATE_TCP_CLIENT = {'cmd': 'AT+WIPCREATE=2,1,"185.41.186.74",2021\r\n', 'cmd_resp': 'OK', 'time_out': 6000,
                                 'delay': 0, 'skip': 0}
        self.cmd_READ_DATA = {'cmd': 'AT+WIPDATA=2,1,1\r\n', 'cmd_resp': 'CONNECT', 'time_out': 6000, 'delay': 0, 'skip': 0}

        self.cmd_STOP_READ_DATA = {'cmd': '+++', 'cmd_resp': 'CONNECT', 'time_out': 6000, 'delay': 0, 'skip': 0}

    # Подключаем канал GPRS, возвращает True и переходит в режим чтения данных
    def connect_to_gprs(self):
        # Настройка соеденения
        self.uGSM = UART(1, baudrate=115200, rx=22, tx=23, timeout=3000)
        #self.uGSM.callback(self.uGSM.CBTYPE_PATTERN, self.uart_cb_func, pattern=b'\r\n')
        print("connect to device...")
        res = self.send_at_req(self.cmd_AT)
        if(res == True):
            self._f_device_ok = True
            print("connect to device ok")
            res = self.send_at_req(self.cmd_START_IP_STACK)
            if(res == False):
                return False
            res = self.send_at_req(self.cmd_OPEN_GPRS_BR)
            if (res == False):
                return False
            res = self.send_at_req(self.cmd_APN_GPRS_BR)
            if (res == False):
                return False
            res = self.send_at_req(self.cmd_START_GPRS_BR)
            if (res == False):
                res = self.send_at_req(self.cmd_STOP_GPRS_BR)
                #return False
            res = self.send_at_req(self.cmd_CREATE_TCP_CLIENT)
            if (res == False):
                return False
            res = self.send_at_req(self.cmd_READ_DATA)
            if (res == False):
                return False
            self._f_read_data_from_server = True
            return True
        else:
            # 
            print("device not work")
    # Отключаем режим GPRS, режим AT команд
    def disconnect_gprs(self):
        time.sleep(2)
        self.send_at_req(self.cmd_STOP_READ_DATA)
        time.sleep(2)
        self.send_at_req(self.cmd_AT)
        self.send_at_req(self.cmd_STOP_GPRS_BR)
        self.send_at_req(self.cmd_CLOSE_GPRS_BR)
        self.uGSM.flush()
        return self.send_at_req(self.cmd_STOP_IP_STACK)


    def send_data_to_server(self,data):
        self.uGSM.flush()
        data = ujson.dumps(data)
        print("send_data_to_server data = ",data)
        if (type(data) == str):
            data = data+"\n"
            self.uGSM.write(data.encode())
        else:
            self.uGSM.write(data)

    def uart_cb_func(self,res):
        # Ф-ция обратного вызова при приеме данных через UART
        # сдесь нужно разделять в каком режиме работает модем,
        # если это прием через gprs, обрабатываем данные
        print("uart_cb_func: ",res)
        if(res[0]==3):
            # Ошибка
            pass
        else:
            # Обрабатываем данные
            if(self._f_read_data_from_server == True):
                # Пришли данные с сервера
                pass
            else:
                # Пришли данные, обрабатываем запросс к модему
                if(res[2]==self._responce):
                    self._f_resp_ok = True
                #else:
                pass
        pass

    def _get_str_from_line(self,ln):
        # удаляем из строки перенос
        if (ln != None):
            stroka = ln.split('\r\n')
            try:
                while(True):
                    stroka.remove('')
            except ValueError:
                #print("except ValueError in _get_str_from_line is ok")
                pass
            if (len(stroka) > 0):
                print("_get_str_from_line(self,ln) len(stroka) > 0")
                return stroka[0]
            else:
                print("_get_str_from_line(self,ln) len(stroka) = 0")
                return None
        return None

    def cb_exec_at_data(self,data):
        # проверяем какая команда пришла
        print(data)
        pass

    # процесс обработки данных в режиме AT
    def proc_at_data(self):
        stroka = self._get_str_from_line(self.uGSM.readln(1000))
        if(stroka != None):
            # проверяем данные
            # может быть вызов
            # а также проверка смс
            if (self.cb_exec_server_data != None):
                self.cb_exec_at_data(stroka)
        else:
            self.uGSM.flush()
            # здесь проверяем наличие новых смс
            self.uGSM.write('AT+CMGL="ALL"\r\n')
            stroka = self._get_str_from_line(self.uGSM.readln(1000))
            ans = list()
            while(stroka!=None):
                # Для начала ищем в строрке +CMGL
                # если да - это шапка и первая строка
                # удаляем '+CMGL: ', раскладываем через разделители ','
                # 1- номер сообщения, 2 - флаг состояния(прочитано или нет)
                # 3 - номер телефона, 4 название в симкарте
                # 5 Service Center Time Stamp
                # дальше перевод строки, и текст сообщения
                ans.append(stroka[0])
                ans.append(stroka[1])
                ans.append(stroka[2])
                ans.append("")
                ans.append("")
                ans.append("")
                # если не найдена строка '+CMGL: ', скорее всего это текст сообщения
                stroka = self._get_str_from_line(self.uGSM.readln(1000))
                pass

    def proc_server_data(self):
        # чтение данных, задержка на чтение в течении 2 сек
        stroka = self._get_str_from_line(self.uGSM.readln(2000))
        if(stroka != None):
            # передаем строку на обработку
            # print("proc_server_data - ",stroka)
            if(self.cb_exec_server_data !=None):
                self.cb_exec_server_data(stroka)

    def send_at_req(self,at_cmd):
        # Отправляем ат команду
        self._responce = at_cmd['cmd_resp']
        self._f_resp_ok = False
        self.uGSM.write(at_cmd['cmd'])
        read_str = self.uGSM.readln(at_cmd['time_out'])
        while(read_str!= None):
            read_str = read_str.split()
            #print(read_str)
            if(len(read_str)>0):
                if(read_str[0] == at_cmd['cmd_resp']):
                    self._f_resp_ok = True
                    self.uGSM.flush()
                    break
            read_str = self.uGSM.readln(at_cmd['time_out'])
        return self._f_resp_ok
        pass