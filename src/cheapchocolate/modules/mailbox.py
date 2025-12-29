import os
from cheapchocolate.core import config


def get_local_mails():
    mails = []
    for mail_file in os.listdir(get_local_mailbox_folder()):
        mail_file.split(" - ")[0]
        mails.append(mail_file.split(" - ")[0])
    return mails


def get_local_mailbox_folder():
    mailbox_folder = config.get_dir("mailbox")
    return mailbox_folder
