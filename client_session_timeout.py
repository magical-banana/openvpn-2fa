#!/usr/bin/env python

# REQUIREMENTS: - OpenVPN must be listening on its TCP management interface.
#                 See: https://openvpn.net/index.php/open-source/documentation/miscellaneous/79-management-interface.html
#               - netcat is installed
#               - logger is installed

import re
import os
from datetime import datetime

if os.geteuid() != 0:
    exit("You need run this script as root. Exiting.")

client_status_log="/var/log/openvpn/status.log"

# Change this to change the maximum session length
timeout_seconds = 8*60*60

mgmt_connect_string="nc localhost 7505"

# END CONFIG - Don't edit below this line #

now = int(datetime.now().strftime("%s"))
kill_list = []

with open(client_status_log) as inf:
    for line in inf:
        line = line.rstrip()
        if "ROUTING TABLE" in line:
            break
        if re.match(r".*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*",line):
            fields = line.split(",")
            username = fields[0]
            ip_addr = fields[1]
            conn_start_hr = fields[4]
            conn_start = int(datetime.strptime(fields[4], '%Y-%m-%d %H:%M:%S').strftime("%s"))
            if ( now - conn_start > timeout_seconds ):
                kill_list.append({'username':username, 'ip_addr':ip_addr, 'conn_start':conn_start, 'conn_start_hr':conn_start_hr})
    for client in kill_list:
        kill_string = "echo 'kill "+client['ip_addr']+"'|"+mgmt_connect_string
        logger_string = "echo 'INFO=>[OpenVPN timeout script] " + \
            datetime.fromtimestamp(now).strftime('%a %b %d %H:%M:%S %Y') + \
            " Killing client connected as " + \
            str(client['ip_addr']) + \
            " with connection start at " + \
            client['conn_start_hr'] + \
            "'|logger"
        # Kill client
        os.system(kill_string)
        # Log this event to syslog
        os.system(logger_string)