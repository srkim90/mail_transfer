import gzip
import os
import platform
import random
import smtplib
import threading
from typing import Union, List


class MailSendService:
    def __init__(self, server_host: str, port: int, sender_uid: str, sender_pw: str) -> None:
        super().__init__()
        self.server_host = server_host
        self.port = port
        self.sender_uid = sender_uid
        self.sender_pw = sender_pw
        self.max_thread = 10
        if "window" in platform.system().lower():
            self.base_path = "D:\\data\\terracehamadm"
        else:
            self.base_path = "/opt/mail-migration-data/terracehamadm"

    @staticmethod
    def read_qs(mail_path: str) -> bytes:
        mail_data: bytes
        if mail_path.split(".")[-1].lower() == "gz":
            fd = gzip.open(mail_path, "rb")
        else:
            fd = open(mail_path, "rb")
        mail_data = fd.read()
        new_data: bytes = b''
        for idx, line in enumerate(mail_data.split(b'\n')):
            if idx == 0:
                continue
            if b'^^^^^^^^+_~!spacelee@$%^&!@#)_,$^^^^^^^^^^' in line:
                break
            new_data += line + b'\n'
        fd.close()
        return new_data

    def __send_mail_smtp(self, smtp:smtplib.SMTP, from_addr: str, to_addrs: str, message:bytes) -> None:
        smtp.sendmail(from_addr=self.sender_uid, to_addrs=to_addrs, msg=message)

    def __start_stat(self, smtp:smtplib.SMTP, from_addr: str, to_addrs: str, message:bytes) -> threading.Thread:
        h_thread = threading.Thread(target=self.__send_mail_smtp, args=(smtp, from_addr, to_addrs, message))
        h_thread.daemon = True
        h_thread.start()
        return h_thread

    def __mail_paths_add(self, receiver_addrs: Union[str, List[str]], mail_paths: Union[str, List[str]]):
        if type(receiver_addrs) == list and type(mail_paths) == list:
            ln_receivers = len(receiver_addrs)
            ln_mails = len(mail_paths)
            if ln_receivers > ln_mails:
                shortage = ln_receivers - ln_mails
                add_mail = mail_paths[0:shortage]
                return mail_paths + add_mail
        return mail_paths

    def send_mail(self, receiver_addrs: Union[str, List[str]], mail_paths: Union[str, List[str]], to_all: bool):
        if type(mail_paths) == str:
            mail_paths = [mail_paths, ]
        if len(mail_paths) == 0:
            print("Not exist mail to send : base_path=%s" % (self.base_path,))
            return
        if type(receiver_addrs) == str:
            receiver_addrs = [receiver_addrs,]
        mail_paths = self.__mail_paths_add(receiver_addrs, mail_paths)
        smtps = [None] * self.max_thread
        t_threads = []
        n_send_mails = 0
        for idx, mail_path in enumerate(mail_paths):
            smtp = smtps[idx % self.max_thread]
            if smtp is None:
                smtp = smtplib.SMTP(self.server_host, self.port)
                smtp.login(self.sender_uid, self.sender_pw)
            message = self.read_qs(mail_path)
            rr_idx = idx % len(receiver_addrs)
            #smtp.sendmail(from_addr=self.sender_uid, to_addrs=receiver_addrs[rr_idx], msg=message)
            receiver_addr_at = receiver_addrs[rr_idx]
            if to_all is True:
                receiver_addr_at = receiver_addrs
            t_threads.append(self.__start_stat(smtp, self.sender_uid, receiver_addr_at, message))
            remain = len(mail_paths) - (idx + 1)
            print("send mail : [%d/%d] %s" % (idx, len(mail_paths), mail_path))
            n_send_mails += 1
            #if idx % 10 == 0 and idx != 0:
            if len(t_threads) >= self.max_thread or remain == 0:
                f_reset_smtp = False
                if n_send_mails > self.max_thread * 10:
                    n_send_mails = 0
                    f_reset_smtp = True
                for jdx, t_thread in enumerate(t_threads):
                    t_thread.join()
                    if f_reset_smtp is True:
                        smtp = smtps[jdx]
                        if smtp is not None:
                            smtp.close()
                        smtps[jdx] = None
                t_threads = []


    def load_mail_data(self, load_count: int = -1) -> List[str]:
        result = []
        mail_fills = []
        if os.path.exists(self.base_path) is False:
            return []
        for (root, dirs, files) in os.walk(self.base_path):
            for item in files:
                if ".qs" not in item:
                    continue
                full_path = os.path.join(root, item)
                if os.stat(full_path).st_size > 1024 * 1024:
                    continue
                mail_fills.append(full_path)
        random.shuffle(mail_fills)
        for idx, mail_item in enumerate(mail_fills):
            if load_count != -1 and load_count <= idx:
                break
            result.append(os.path.join(self.base_path, mail_item))
        return result


def send_all(mail_to: Union[str, List[str]], to_all: bool, n_send_mail: int = -1):
    e = MailSendService("127.0.0.1", 25, "srkim@abctest.co.co", "*************")
    mail_list = e.load_mail_data(n_send_mail)
    e.send_mail(mail_to, mail_list, to_all)
    return


if __name__ == "__main__":
    mail_to = "srkim@abctest.co.co"
    n_send_mail = 10
    send_all(mail_to, False, n_send_mail)
