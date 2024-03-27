import meraki 
import argparse
import json
import csv
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Handel the Args 
parser = argparse.ArgumentParser(description="SSH's and Outputs the following commands Show run-config, Show run-config commands(startup Configs), Show tech, Show mslog into files for TAC")
#parser.add_argument("-merakiconfig", action="store", dest="merakiconfig")
parser.add_argument("-switchlist", action="store", dest="switchlist")
parser.add_argument("-orgid", action="store", dest="orgid")
parser.add_argument("-networkname" , action="store", dest="networkname")
args = parser.parse_args()

#merakiconfig = args.merakiconfig
switchlist = args.switchlist
networkname = args.networkname
orgid = args.orgid

dashboard = meraki.DashboardAPI(log_path='Logs/')


def getNetworkID(orgID, networkName):
    #Get Network ID
    allNetworks = dashboard.organizations.getOrganizationNetworks(orgID)
    for network in allNetworks:
        if network['name'] == networkName:
            netID = network['id']
            logging.info(f"Network ID {netID} Found for Network Named {networkName}")
    
    return netID


def find_configFile(directory, swSN, endString):
    found_files = ''
    def find_files_with_string(directory, mid_string, end_string):
        files =  os.listdir(directory)
        mid_string = mid_string.strip()
        for filename in files:
            if mid_string.lower() in filename.lower():
                found_files = filename
                logging.info(f"Matching (SN: {mid_string}) Config File Found {filename}")
        return found_files
    
    result = find_files_with_string(directory, swSN, endString)
    return result



def claimAndConfigSwitchStack (netID, stackName, serialNums, mkconfig):
    #Claim Serial numbers
    dashboard.networks.claimNetworkDevices(netID, serials=serialNums)
    
    with open('Meraki-Config/'+mkconfig, 'r') as configFile:
        swinterfaceConfig = json.load(configFile)
    
    #Configure individual switch name and switch ports    
    for swnum, serial in enumerate(serialNums):
        
        actionList = []
        realSWNum = swnum+1

        #Configure Switch Name
        dashboard.devices.updateDevice(serial, name=f"{stackName}-{realSWNum}")
        logging.info(f"Name Switch: {stackName}-{realSWNum} - Serial Number: {serial}")
        for interface, intConfig in swinterfaceConfig.items(): 
            if interface == "0/0":
                ##Ignore MGMT INT
                None
            else:
                interfaceName = interface
                switch, module, port = map(int, interfaceName.split("/"))
                #logging.debug(f"Port Config: {interfaceName} - Switch# {switch} - Interface Config {intConfig}")
                if switch == realSWNum and module == 0:
                    # Model = 0  should be 1-24 or 1-48?
                    merakiPortID = port-1
                    if intConfig != {}:
                        # Adds Port Config to Action List
                        actionList.append(dashboard.batch.switch.updateDeviceSwitchPort(serial, merakiPortID, **intConfig))
       
        ABMessage = dashboard.organizations.createOrganizationActionBatch(orgid, actions=actionList, synchronous=True, confirmed=True) 
        #Submit Action Batch for port config. 
        logging.debug(f"Action Batch Details: {ABMessage}")

    if len(serialNums) > 1:
        #Configure Switch Stacks 
        dashboard.switch.createNetworkSwitchStack(netID, stackName, serials=serialNums)
        

def find_serial_numbers(row):
    # Define the pattern for the serial number (assuming it consists of three groups of four characters separated by hyphens)
    serial_pattern = r'[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}'
    
    # List to store found serial numbers
    serial_numbers = []
    
    # Iterate over each column
    for column in row:
        # Check if the column value matches the serial number pattern
        matches = re.findall(serial_pattern, column)
        # If matches are found, extend the serial_numbers list
        if matches:
            serial_numbers.extend(matches)
    
    print(f"Serial Numbers: {serial_numbers}")
    return serial_numbers

def main():
    with open(switchlist, 'r', newline='') as switchFileRead:
        #switchlistconfig =  json.loads(switchFile)
        reader = csv.reader(switchFileRead)
        rows = list(reader)
        
        for index, row in enumerate(rows[1:]): 
            switchIP = row[0]

            if row[1] == "BackedUp":
                # Find Meraki Config where first serial is in config filename

                # Claim Switches, Create Stack
                # Configure switchports
                mkconfig = find_configFile('Meraki-Config', row[5], "-mkconf.json")
                networkID = getNetworkID(orgid, networkname)
                mkserials = find_serial_numbers(row)
                claimAndConfigSwitchStack (networkID, row[2], mkserials, mkconfig)

                row[1] = "Configured"

            else:
                print(f"Switch: {row[0]} was not Configured")

    ## Update CSV with Rows that were 'Configured'            
    with open(switchlist, 'w', newline='') as switchFileWrite:
        writer = csv.writer(switchFileWrite)
        writer.writerows(rows)

if __name__ == "__main__":
    main()