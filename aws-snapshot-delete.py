import sys
import boto3
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import datetime, timedelta

try:
        days = int(sys.argv[1])
except IndexError:
        days = 30

sns_arn = 'SNS ARN'
delete_time = datetime.utcnow() - timedelta(days=days)

today = datetime.today ()
tday = today.strftime ("%m-%d-%Y")

print('Deleting any snapshots older than {days} days'.format(days=days))

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

result = ec2.describe_snapshots(OwnerIds=['self'])

deletion_counter = 0
size_counter = 0

for snapshot in result['Snapshots']:
        snapshot_time = snapshot['StartTime'].replace(tzinfo=None)
        snapshot_id = snapshot['SnapshotId']
        print ("%s %s" %(snapshot['SnapshotId'],snapshot['StartTime']))
        print(delete_time)
        print(snapshot_time)

        if snapshot_time < delete_time:
                print('Deleting {snapshot_id}'.format(snapshot_id = snapshot['SnapshotId']))
                deletion_counter = deletion_counter + 1
                size_counter = size_counter + snapshot['VolumeSize']
                # Just to make sure you're reading!
                ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
                print({SnapshotId})
                
mail_body = "################Snaphost#################"
mail_body = mail_body + "\n\nTotal Deleted Snapshots Size:{}".format(size_counter)
mail_body = mail_body + "\n\nTotal Deleted Snapshot Count: {}".format(deletion_counter)

print('Deleted {number} snapshots totalling {size} GB'.format(
        number=deletion_counter,
        size=size_counter
))


sns.publish(
    TopicArn = sns_arn,
    Subject = 'Snapshot Clean up',
    Message = mail_body
    )
print(mail_body)

# Replace sender@example.com with your "From" address.
# This address must be verified.
SENDER = 'SES'
SENDERNAME = 'Snapshot'

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
RECIPIENT  = 'YOUR ID'

# Replace smtp_username with your Amazon SES SMTP user name.
USERNAME_SMTP = "KEEP SMTP ACCESS"

# Replace smtp_password with your Amazon SES SMTP password.
PASSWORD_SMTP = "KEEP SMTP PASSWORD"

# (Optional) the name of a configuration set to use for this message.
# If you comment out this line, you also need to remove or comment out
# the "X-SES-CONFIGURATION-SET:" header below.
#CONFIGURATION_SET = "ConfigSet"
#
# If you're using Amazon SES in an AWS Region other than US West (Oregon),
# replace email-smtp.us-west-2.amazonaws.com with the Amazon SES SMTP
# endpoint in the appropriate region.
HOST = "AZ EMAIL"
PORT = 587

# The subject line of the email.
SUBJECT = "AWS Snapshot Deletion Summary -" + str(today.strftime("%d/%m/%y"))

# The email body for recipients with non-HTML email clients.
BODY_TEXT = ("Deleted Snapshots\r\n"
            )

# The HTML body of the email.
BODY_HTML = """<html>
<head></head>
<body>
  <h1>AWS Snapshot Deleted Status</h1>
  <p>Snapshot Delete</p>
                <meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'>
                <title>SNAPSHOT Delete Status</title>
                <STYLE TYPE="text/css">
                <!--
                td {
                font-family: Tahoma;
                font-size: 11px;
                border-top: 1px solid #999999;
                border-right: 1px solid #999999;
                border-bottom: 1px solid #999999;
                border-left: 1px solid #999999;
                padding-top: 0px;
                padding-right: 0px;
                padding-bottom: 0px;
                padding-left: 0px;
                overflow: hidden;
                }
                body {
                margin-left: 5px;
                margin-top: 5px;
                margin-right: 0px;
                margin-bottom: 10px;
                table {
                table-layout:fixed;
                border: thin solid #000000;

                }
                -->
                </style>
                </head>
                <body>
                <table width='1200'>
                <tr bgcolor='#CCCCCC'>
                <td colspan='7' height='48' align='center' valign="middle">
                <font face='tahoma' color='#003399' size='4'>
                <strong><u>SNAPSHOT Delete Stauts - """ + tday + """</u></strong></font>
                </td>
                </tr>
                </table>
                <table width='1200'><tbody>
                        <tr  height='35'>
                        <td bgcolor=#FCF7F6 width='6%' align='center'><strong></strong></td>
                    <td bgcolor=#F7F6D7 width='6%' align='center'><strong>Count</strong></td>
                        <td bgcolor=#F7F6D7 width='6%' align='center'><strong>TotalSize (GB)</strong></td>
                        </tr>
        <tr height='35'>
        <td bgcolor=#F7F6D7 width='6%' align='center'><strong>Deleted Successfully</strong></td>
        <td bgcolor=#A4EC8A width='6%' align='center'><strong>""" + "{}".format(deletion_counter) + """</strong></td>
        <td bgcolor=#A4EC8A width='6%' align='center'><strong>""" + "{}".format(size_counter) + """</strong></td>
        </tr>
</body>
</html>
            """

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = SUBJECT
msg['From'] = email.utils.formataddr((SENDERNAME, SENDER))
msg['To'] = RECIPIENT
# Comment or delete the next line if you are not using a configuration set
#msg.add_header('X-SES-CONFIGURATION-SET',CONFIGURATION_SET)

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(BODY_TEXT, 'plain')
part2 = MIMEText(BODY_HTML, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Try to send the message.
try:
    server = smtplib.SMTP(HOST, PORT)
    server.ehlo()
    server.starttls()
    #stmplib docs recommend calling ehlo() before & after starttls()
    server.ehlo()
    server.login(USERNAME_SMTP, PASSWORD_SMTP)
    server.sendmail(SENDER, RECIPIENT, msg.as_string())
    server.close()
# Display an error message if something goes wrong.
except Exception as e:
    print ("Error: ", e)
else:
    print ("Email sent!")
