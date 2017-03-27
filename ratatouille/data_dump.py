from ratatouille.models import Logging
import csv
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

from django.conf import settings

settings.configure()


emailfrom = "doremonnlp@gmail.com"
emailto = "prakhar.0892@gmail.com"
fileToSend = "text.csv"
username = "doremonnlp@gmail.com"
password = "casper08"

list_logs = Logging.objects.all()

with open('text.csv', 'w') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
    csv_writer.writerow(("asr_text", "asr_time", "nlu_text", "nlu_time", "errorCode", "pre", "action", "count"))
    for ll in list_logs:
        if ll.action is not None:
            action = ll.action
        else:
            action = -1
        print "Action: " + str(action)
        if ll.count is not None:
            count = ll.count
        else:
            count = -1
        print "Count: " + str(count)
        if ll.pre is not None:
            pre = ll.pre
        else:
            pre = -1
        print "Pre: " + str(pre)
        if ll.errorCode is not None:
            errorCode = ll.errorCode
        else:
            errorCode = -1
        print "Error code: " + str(errorCode)
        if ll.asr_text is not None:
            asr_text = ll.asr_text
        else:
            asr_text = ""
        print "ASR Text: " + str(asr_text)
        if ll.nlu_text is not None:
            nlu_text = ll.nlu_text
        else:
            nlu_text = ""
        print "NLU Text: " + str(nlu_text)
        if ll.asr_time is not None:
            asr_time = ll.asr_time
        else:
            asr_time = ""
        print "ASR Time: " + str(asr_time)
        if ll.nlu_time is not None:
            nlu_time = ll.nlu_time
        else:
            nlu_time = ""
        print "NLU Time: " + str(nlu_time)
        csv_writer.writerow((asr_text, asr_time, nlu_text, nlu_time, errorCode, pre, action, count))


msg = MIMEMultipart()
msg["From"] = emailfrom
msg["To"] = emailto
msg["Subject"] = "Data dump"
msg.preamble = "help I cannot send an attachment to save my life"

ctype, encoding = mimetypes.guess_type(fileToSend)
if ctype is None or encoding is not None:
    ctype = "application/octet-stream"

maintype, subtype = ctype.split("/", 1)

if maintype == "text":
    fp = open(fileToSend)
    # Note: we should handle calculating the charset
    attachment = MIMEText(fp.read(), _subtype=subtype)
    fp.close()
elif maintype == "image":
    fp = open(fileToSend, "rb")
    attachment = MIMEImage(fp.read(), _subtype=subtype)
    fp.close()
elif maintype == "audio":
    fp = open(fileToSend, "rb")
    attachment = MIMEAudio(fp.read(), _subtype=subtype)
    fp.close()
else:
    fp = open(fileToSend, "rb")
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(attachment)
attachment.add_header("Content-disposition", "attachment", filename=fileToSend)
msg.attach(attachment)

server = smtplib.SMTP("smtp.gmail.com:587")
server.starttls()
server.login(username,password)
server.sendmail(emailfrom, emailto, msg.as_string())
server.quit()