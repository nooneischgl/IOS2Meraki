"""
convertIOS2Meraki.py
This script convers IOS Restconf config into Meraki Switchport config
"""

import json
import logging

iosJson = {}
merakiJson = {}

def convertConfig(iosconfig, merakiconfig ):

    with open(iosconfig, 'r') as configFile:
        iosJson = json.load(configFile)

    ## Creat JSON config per switch port

    GigEth = iosJson['data']['Cisco-IOS-XE-native:native']['interface']['GigabitEthernet']
    # Todo add other interface types
    #showRun['data']['Cisco-IOS-XE-native:native']['interface']['TenGigabitEthernet']


    for interface in GigEth:
        merakiInt = {}
        intNumber = interface['name']
        #merakiInt['portID'] = intNumber
        print(f"INTERFACE: {interface}")
        if 'description' in interface:
            intDescription = interface['description']
            merakiInt['name'] = intDescription
        if 'shutdown' in interface:
            if interface['shutdown'] == [None]:
                merakiInt['enabled'] = False
            intEnable = interface['shutdown']
        ### Need to account for admin down / disabled ports ##
        ## Only Layer 2 Switchport Config
        if 'switchport-config' in interface:
            intType = interface['switchport-config']['switchport']
            print('switchport')
            if 'Cisco-IOS-XE-switch:mode' in intType:
                print('switch-mode')
                if intType['Cisco-IOS-XE-switch:mode']  ==  {'trunk': {}}:
                    print('trunk')
                    intTypeTrunk = ''
                    if 'Cisco-IOS-XE-switch:trunk' in intType:
                        intTypeTrunk = intType['Cisco-IOS-XE-switch:trunk']
                    #Trunk Logic
                    if 'native' in intTypeTrunk:
                        nativeVlan = intTypeTrunk['native']['vlan']['vlan-id']
                        merakiInt['vlan'] = nativeVlan
                    if 'allowed' in intTypeTrunk:
                        allowedVlans = intTypeTrunk['allowed']['vlan']['vlans']
                        merakiInt['allowedVlans'] = allowedVlans
                    merakiInt['type'] = 'trunk'

                elif intType['Cisco-IOS-XE-switch:mode'] == {'access': {}}:
                    #Access Logic
                    intTypeAccess = intType['Cisco-IOS-XE-switch:access']
                    if 'vlan' in intTypeAccess:
                        accessVlan = intTypeAccess['vlan']['vlan']
                        merakiInt['vlan'] = accessVlan
                    if 'voice' in intTypeAccess:
                        voiceVlan = intTypeAccess['voice']['vlan']
                        merakiInt['voiceVlan'] = voiceVlan
                    merakiInt['type'] = 'access'

                else:
                    #Assume Access
                    merakiInt['type'] = 'access'
        print(f"Meraki INT: {merakiInt}")

        merakiJson[f'{intNumber}'] = merakiInt
        print(merakiInt)

    interfaces_details = merakiJson

    def interface_key(interface):
        # Special case for interface "0/0"
        if interface == "0/0":
            return (-1, -1)  # Ensuring "0/0" comes first
        # Split the interface into switch, module, and port, and convert them to integers
        switch, module, port = map(int, interface.split("/"))
        return (switch, module, port)

    # Sort the dictionary by its keys using the interface_key function
    sorted_interfaces_details = dict(sorted(interfaces_details.items(), key=lambda item: interface_key(item[0])))
    logging.debug(f"Interface Details: {sorted_interfaces_details}")


    with open(f'{merakiconfig}', 'w') as configFile:
        json.dump(sorted_interfaces_details, configFile, indent=2)
        ## Find Access or Trunk
            ## Access: Data and Voice VLANs
            ## Trunk: Native and Allowed VLANs
            ## Future PortChannel Add

        ## Stack handeling, looks like port ID on Merkai even in a stack are 1 - 52 yay
            ## just need to handel module uplink to portid Mapping
            ## serial nunmber to port id mapping
                   
def main():
    convertConfig()

if __name__ == "__main__":
    main()