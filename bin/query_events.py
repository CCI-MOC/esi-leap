"""
Description:
This script is designed to query and send email notifications for ESI lease events.

Usage:
To run this script, execute it from CLI or add it to a scheduled task (like cronjob).
Before running, ensure the following environment variables are set:
    - ENABLE_EMAIL: Set to 'true' to enable email notifications. Default is 'false'.
    - SMTP_SERVER: Hostname of the SMTP server for sending emails. Default is 'localhost'
    - EMAIL_SENDER: The email address that will be used as the sender in outgoing emails
    - LEASE_WARNING_DAYS: Number of days before a lease's end when a notification email should be sent
    - LEASE_CREATE_TEMPLATE: File path to the email template for lease creation notifications
    - LEASE_EXPIRE_TEMPLATE: File path to the email template for lease expiration warnings

Example:
$ python query_event.py
"""

import datetime
from dateutil import parser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import subprocess
import smtplib


enable_email = os.getenv('ENABLE_EMAIL', 'false').lower() == 'true'
smtp_server = os.getenv('SMTP_SERVER', 'localhost')
email_sender = os.getenv('EMAIL_SENDER')
lease_warning_days = int(os.getenv('LEASE_WARNING_DAYS', 1))
lease_create_template = os.getenv('LEASE_CREATE_TEMPLATE', 'lease_create_email.txt')
lease_expire_template = os.getenv('LEASE_EXPIRE_TEMPLATE', 'lease_expire_email.txt')


def run_openstack_command(cmd):
    output_json = subprocess.check_output('%s --format json' % cmd, shell=True)
    return json.loads(output_json)

def get_last_event_id(default_last_event_id=0, file_name='.esi-last-event-id'):
    try:
        with open(file_name, "r") as f:
            last_event_id = int(f.read())
    except FileNotFoundError:
        last_event_id = default_last_event_id
    except ValueError:
        last_event_id = default_last_event_id
    return last_event_id

def write_last_event_id(last_event_id, file_name='.esi-last-event-id'):
    with open(file_name, "w") as f:
        f.write(str(last_event_id))

def notify_lease(project_name, email_body):
    try:
        project = run_openstack_command('openstack project show %s' % project_name)
        to_email = project.get('email')
        if not to_email:
            print('No email linked to project %s. '
                  'Not sending email notification' % project)
        else:
            msg = MIMEMultipart()
            msg['From'] = email_sender
            msg['To'] = to_email
            msg['Subject'] = '[ESI]Lease notification'
            msg.attach(MIMEText(email_body, 'plain'))
            server = smtplib.SMTP(smtp_server)
            server.sendmail(email_sender, to_email,
                            msg.as_string())
            server.quit()
            print("Email sent successfully to %s" % to_email)
    except Exception as e:
        print('Email not sent: %s: %s' %
                (type(e).__name__, e))

def fill_email_template(template_path, **kwargs):
    try:
        with open(template_path, 'r') as f:
            content = f.read()
            return content.format(**kwargs)
    except FileNotFoundError:
        print("email template path not found")

def main():
    last_event_id = get_last_event_id()
    events = run_openstack_command('openstack esi event list --last-event-id %s' % last_event_id)
    new_last_event_id = last_event_id
    # checking for leases fulfillment
    for event in events:
        new_last_event_id = event['ID']
        if event['Event Type'] == 'esi_leap.lease.fulfill.end':
            node_uuid = event['Resource UUID']
            lease_uuid = event['Object UUID']
            lease = run_openstack_command('openstack esi lease show %s' % lease_uuid)
            print("Lease %s with purpose %s on node %s started" % (lease_uuid, lease['purpose'], node_uuid))
            if enable_email:
                email_body_lease_start = fill_email_template(lease_create_template,
                                                             project=lease['project'],
                                                             lease_uuid=lease['uuid'],
                                                             start_time=lease['start_time'],
                                                             end_time=lease['end_time'],
                                                             node_name=lease['resource'],
                                                             node_uuid=lease['resource_uuid'])
                notify_lease(lease['project'], email_body_lease_start)
    write_last_event_id(new_last_event_id)

    # Checking for leases expire soon
    leases = run_openstack_command('openstack esi lease list --all')
    now = datetime.datetime.utcnow()
    for lease in leases:
        lease_end = parser.parse(lease["End Time"])
        if lease_end - now <= datetime.timedelta(lease_warning_days):
            print('Lease %s is expiring in %s day(s)' %(lease["UUID"], lease_warning_days))
            if enable_email:
                email_body_lease_expire = fill_email_template(lease_expire_template,
                                                              project=lease['Project'],
                                                              lease_uuid=lease['UUID'],
                                                              end_time=lease['End Time'],
                                                              node_name=lease['Resource'])
                notify_lease(lease['Project'], email_body_lease_expire)

if __name__ == "__main__":
    main()
