from ftplib import FTP
from config import FTP_ADDR, FTP_USER, FTP_PSWD

# FILE_NAME: str = '1642768729.76900.mp3'

# try:
    # with FTP(FTP_ADDR, FTP_USER, FTP_PSWD) as ftp, open('./'+FILE_NAME, 'rb') as file:
        # ftp.set_pasv(False)
        # ftp.encoding = "utf-8"
        # print(ftp.nlst())
        # print(ftp.storbinary(f"STOR 2_{FILE_NAME}", file))
        # print(ftp.nlst())
# except Exception as e:
    # print(f'Error: {e}')

try:
    with FTP(FTP_ADDR, FTP_USER, FTP_PSWD) as ftp:
        ftp.set_pasv(False)
        ftp.encoding = "utf-8"
        listing_ftp: list = ftp.nlst()
        for i in listing_ftp:
            print(f'{i}')
        # print(ftp.delete('2_'+FILE_NAME))
        # print(ftp.nlst())
except Exception as e:
    print(f'Error: {e}')
