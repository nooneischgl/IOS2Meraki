"""
backupSWconfig.py
This script backs up IOSXE Switch config (in RestJSON format) and converts switchport config into Meraki JSON.
Config Files saved in IOS-Config/ and Meraki-Config dirs accordingly
"""

import os
from netmiko import ConnectHandler
import argparse
import csv
import json
import textfsm
import convertIOS2Meraki
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Handel the Args 
parser = argparse.ArgumentParser(description="SSH's and Outputs the following commands Show run-config, Show run-config commands(startup Configs), Show tech, Show mslog into files for TAC")
#parser.add_argument("-username", action="store", dest="username")
#parser.add_argument("-password", action="store", dest="password")
#parser.add_argument("-enabledPwd", action="store", dest="enabledpwd")
parser.add_argument("-switchlist", action="store", dest="switchlist")
parser.add_argument("-switchip", action="store", dest="switchip")
args = parser.parse_args()

# if not dot env then args 


username = os.getenv("SSH_USERNAME")
password = os.getenv("SSH_PASSWORD")
enabledpwd = os.getenv("SSH_ENABLE")
switchlist = args.switchlist
switchIP = args.switchip

#Show Meraki TextFSM
template = 'cisco_ios_show_meraki_partial.textfsm'
### Load the template
with open(template, 'r') as template_file:
    template = textfsm.TextFSM(template_file)


#Open Switch List File
if switchlist:
    with open(switchlist, mode='r') as swList:
        reader = csv.reader(swList) 
        rows = list(reader)
        

        for index, row in enumerate(rows[1:]): 
            print(f"ROW: {row}")
            logging.info(f"Switch List Row: {row}")

            switchIP = row[0]

            #Dont back up if already configured or backedup
            if row[1] not in ["BackedUp","Configured"]:    

                switchCon = {
                    'device_type': 'cisco_ios',
                    'host': switchIP,
                    'username': username,
                    'password': password,
                    'secret': enabledpwd
                }

                sw_connect = ConnectHandler(**switchCon)
                # Run commands on switch 
                showVersion = sw_connect.send_command('show version',use_textfsm=True)
                showMeraki = sw_connect.send_command('show meraki',use_textfsm=True)
                showRun = json.loads(sw_connect.send_command('show running-config | format restconf-json', read_timeout=240))

                formattedShowMerkai = template.ParseText(showMeraki)

                logging.debug(f"Show Verison {showVersion}")
                logging.debug(f"Show Meraki: {formattedShowMerkai}")

                swHostname = showVersion[0]['hostname']
                swCatSerial = showVersion[0]['serial']

                # Save Config Files 
                iosconfig = f'IOS-Config/{swHostname}-{"-".join(swCatSerial)}-restconf.json'
                merakiconfig = f'Meraki-Config/{swHostname}-{"-".join(swCatSerial)}-mkconf.json'
                with open(iosconfig, 'w') as configFile:
                    json.dump(showRun, configFile, indent=2)

                convertIOS2Meraki.convertConfig(iosconfig, merakiconfig)

                #Update CSV with swith details
                flattenedShowMeraki = [item for sublist in formattedShowMerkai for item in sublist]
                unwanted_chars = '[]"\''
                translation_table = str.maketrans("", "", unwanted_chars)
                sanitizedMeraki = str(flattenedShowMeraki).translate(translation_table)
                rows[index+1] = [row[0],"BackedUp", swHostname, *sanitizedMeraki.split(',')]

            else:
                print(f"Switch: {switchIP} already configured or backedup")
    
    with open(switchlist, 'w', newline='') as switchFileWrite:
        writer = csv.writer(switchFileWrite)
        writer.writerows(rows)




                                                                                                                                   