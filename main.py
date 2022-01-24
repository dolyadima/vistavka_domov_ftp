import os
import hashlib
import requests
import subprocess
import urllib.request
from ftplib import FTP
from mutagen.mp3 import MP3
from datetime import datetime, timedelta
from config import LINE_USER, LINE_PASS, FTP_ADDR, FTP_USER, FTP_PSWD, NEXT_USER, NEXT_PASS

# Translit dict
RU_EN: dict = {'а': 'a', 'б': 'b', 'в': 'v',
               'г': 'g', 'д': 'd', 'е': 'e',
               'ё': 'e', 'ж': 'zh', 'з': 'z',
               'и': 'i', 'й': 'y', 'к': 'k',
               'л': 'l', 'м': 'm', 'н': 'n',
               'о': 'o', 'п': 'p', 'р': 'r',
               'с': 's', 'т': 't', 'у': 'u',
               'ф': 'f', 'х': 'h', 'ц': 'ts',
               'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
               'ь': '', 'ы': 'i', 'ъ': '',
               'э': 'e', 'ю': 'yu', 'я': 'ya'
               }

# Create date,time for request
dt_to = datetime.now()
print(f'---- START {str(dt_to)} ----')
dt_from = dt_to - timedelta(hours=1)

date_from: str = f'{str(dt_from.day).zfill(2)}.{str(dt_from.month).zfill(2)}.{dt_from.year}'  # 31.12.2021
# date_from: str = f'18.01.2022'
date_to: str = f'{str(dt_to.day).zfill(2)}.{str(dt_to.month).zfill(2)}.{dt_to.year}'
time_from: str = f'{str(dt_from.hour).zfill(2)}%3A{str(dt_from.minute).zfill(2)}'  # 23%3A59
# time_from: str = f'14%3A00'
time_to: str = f'{str(dt_to.hour).zfill(2)}%3A{str(dt_to.minute).zfill(2)}'

# Directory of script.py '/root/vistavka_domov_ftp/'
DIR: str = os.path.dirname(os.path.realpath(__file__))

# Connect via web and download report.csv with params date,time,queue
URL: str = 'http://192.168.2.253/cc-line24/admin.php/index.php'
QUERY: dict = {'action': 'login', 'username': LINE_USER, 'password': LINE_PASS}
session = requests.session()
session.get(URL, params=QUERY)
response_vhod = session.get(f'http://192.168.2.253/cc-line24/admin.php/calls/in?date%5Bstart%5D={date_from}+{time_from}&date%5Bend%5D={date_to}+{time_to}&directid%5B0%5D=&queue%5B0%5D=870&agent%5B0%5D=&callerid=&callstatus=answered&uniqueid=&paginator%5Bprev_request_hash%5D=&paginator%5Bpage%5D=1&sort%5Bby%5D=date&sort%5Bdir%5D=asc&export=1')
with open(DIR+'/report_vhod.csv', 'wb') as fw:
    fw.write(response_vhod.content)
response_ishod = session.get(f'http://192.168.2.253/cc-line24/admin.php/calls/out?date%5Bstart%5D={date_from}+{time_from}&date%5Bend%5D={date_to}+{time_to}&agent%5B0%5D=&phone=&calleeid=451&callstatus=answered&uniqueid=&paginator%5Bprev_request_hash%5D=&paginator%5Bpage%5D=1&sort%5Bby%5D=date&sort%5Bdir%5D=asc&export=1')
with open(DIR+'/report_ishod.csv', 'wb') as fw:
    fw.write(response_ishod.content)

# Read data from reports.csv and strip,split
with open(DIR+'/report_vhod.csv', 'r') as file_vhod:
    lines: list = file_vhod.readlines()
stripp: list = [i.strip() for i in lines]  # '\n'
report_vhod: list = [i.split(';') for i in stripp]  # 'date; time; phone... etc'
with open(DIR+'/report_ishod.csv', 'r') as file_ishod:
    lines: list = file_ishod.readlines()
stripp: list = [i.strip() for i in lines]  # '\n'
report_ishod: list = [i.split(';') for i in stripp]  # 'date; time; phone... etc'

# VHOD
# i: 0    1          2          3                      4                5                  6             7         8         9          10        11                                         12
# v: 22 ; 09.01.22 ; 10:00:19 ; Vistavka-Domov-Mango ; Выставка домов ; "Шарапова Елена" ; 89262445801 ; 0:00:12 ; 0:06:40 ; Оператор ; 0:00:30 ; monitor/2022-01-09/1641715219.250757.mp3 ; ""
for i, v in enumerate(report_vhod):
    # skip header
    if i == 0:
        continue

    # translit name
    name_en: str = ''
    for k in v[5].lower():
        name_en += RU_EN.get(k, '')
    v[5] = name_en

    # If file doesn't exist - download file from url and save
    URL: str = f'http://192.168.2.253/cc-line24/{report_vhod[i][11]}'
    NAME: str = report_vhod[i][11].split('/')[2]
    if not os.path.exists(DIR+'/mp3/'+NAME):
        print(f'----- VHOD  -----')

        urllib.request.urlretrieve(URL, DIR+'/mp3/'+NAME)
        PHONE_CLIENT: str = report_vhod[i][6]
        PHONE_AGENT: str = report_vhod[i][5]
        TYPE: str = 'in'
        DATE: str = NAME[:-4].split('.')[0]
        TIMEZONE: str = '2'
        DURATION: str = str(int(MP3(DIR+'/mp3/'+NAME).info.length))
        single_str: str = f'{PHONE_CLIENT}_{PHONE_AGENT}_{TYPE}_{DATE}_{TIMEZONE}_{DURATION}'
        HASH: str = hashlib.md5(single_str.encode()).hexdigest()
        new_name = str(HASH) + '_' + single_str + '.mp3'
        print(f'{report_vhod[i][11]}')
        print(f'{new_name}')
        # [hash]_[phone-client]_[phone-agent]_[type]_[date]_[timezone]_[duration].mp3

        # via bash to nextcloud
        # bashCmd = ['curl', '-k', '-u', NEXT_USER+':'+NEXT_PASS, '-T', DIR+'/mp3/'+NAME, 'https://192.168.2.246/remote.php/webdav/ExhibitionOfHouses/'+new_name]
        # process = subprocess.Popen(bashCmd, stdout=subprocess.PIPE)
        # output, error = process.communicate()

        # via python ftp
        try:
            with FTP(FTP_ADDR, FTP_USER, FTP_PSWD) as ftp, open(DIR+'/mp3/'+NAME, 'rb') as file:
                ftp.set_pasv(False)
                ftp.encoding = "utf-8"
                print(ftp.storbinary(f"STOR {new_name}", file))
        except Exception as e:
            print(f'ftp_error: {e}')

# ISHOD
# i: 0    1          2          3                  4      5                6         7         8                                          9
# v: 12 ; 09.01.22 ; 10:24:47 ; "Шарапова Елена" ; 2066 ; 45189262445801 ; 0:00:11 ; 0:00:46 ; monitor/2022-01-09/1641716684.251509.mp3 ; "Звонок принят"
for i, v in enumerate(report_ishod):
    # skip header
    if i == 0:
        continue

    # translit name
    name_en: str = ''
    for k in v[3].lower():
        name_en += RU_EN.get(k, '')
    v[3] = name_en

    if len(report_ishod[i][5]) > 3 and report_ishod[i][5][:3] == '451':
        # If file doesn't exist - download file from url and save
        URL: str = f'http://192.168.2.253/cc-line24/{report_ishod[i][8]}'
        NAME: str = report_ishod[i][8].split('/')[2]
        if not os.path.exists(DIR+'/mp3/'+NAME):
            print(f'----- ISHOD -----')

            urllib.request.urlretrieve(URL, DIR+'/mp3/'+NAME)
            PHONE_CLIENT: str = report_ishod[i][5][3:]
            PHONE_AGENT: str = report_ishod[i][3]
            TYPE: str = 'out'
            DATE: str = NAME[:-4].split('.')[0]
            TIMEZONE: str = '2'
            DURATION: str = str(int(MP3(DIR+'/mp3/'+NAME).info.length))
            single_str: str = f'{PHONE_CLIENT}_{PHONE_AGENT}_{TYPE}_{DATE}_{TIMEZONE}_{DURATION}'
            HASH: str = hashlib.md5(single_str.encode()).hexdigest()
            new_name = str(HASH) + '_' + single_str + '.mp3'
            print(f'{report_ishod[i][8]}')
            print(f'{new_name}')
            # [hash]_[phone-client]_[phone-agent]_[type]_[date]_[timezone]_[duration].mp3

            # via bash to nextcloud
            # bashCmd = ['curl', '-k', '-u', NEXT_USER+':'+NEXT_PASS, '-T', DIR+'/mp3/'+NAME, 'https://192.168.2.246/remote.php/webdav/ExhibitionOfHouses/'+new_name]
            # process = subprocess.Popen(bashCmd, stdout=subprocess.PIPE)
            # output, error = process.communicate()

            # via python ftp
            try:
                with FTP(FTP_ADDR, FTP_USER, FTP_PSWD) as ftp, open(DIR+'/mp3/'+NAME, 'rb') as file:
                    ftp.set_pasv(False)
                    ftp.encoding = "utf-8"
                    print(ftp.storbinary(f"STOR {new_name}", file))
            except Exception as e:
                print(f'ftp_error: {e}')

print(f'---- END   {str(dt_to)} ----\n')
