# Convert IOSXE Switchport config to Meraki 

Makes in place Migration of C9300 to Meraki Persona Easy!! 
Convert IOSXE to Meraki switches, Switchport configuration to Meraki


- Switch port configuration that **IS** converted
    - Trunk: allowed VLANs and Native VLAN
    - Access: vlan, and voice VLAN
    - Interface descrtion
    - Admin Status

- Switch port configuration NOT Converted
    - LACP / Port Channels 
    - STP commands
    - speed / duplex 


## Reminders when moving from IOS to Meraki Managed 
- Meraki Managed Cat Switches (CS) use a single instance of MSTP
- Access Control / 802.1X is define at a network level then applied per switch port. 

Download BIN File ~1GB (no downtime) ~10 min
Install Command Run time - activate and commit (no downtime - But will auto reload after commit ) ~ 16 min 30 sec
Reload Time ~3 min

Total time ~30 minutes to upgrade 

# Installation

```
git clone
pip install -r requirements
cd ios2meraki/
python backupSWConfig.py -switchlist <switchListFilename.csv>
python configureMerakiSW.py -orgID <MerakiOrgID> -networkName <MerakiNetworkName> -switchlist <switchListFilename.csv>
```

# Usage 
**Add the following Enviorment Varibles for Authentication**
- API Key - `export MERAKI_DASHBOARD_API_KEY=<YOUR_KEY_HERE>`
- SSH username - `export SSH_USERNAME=<SSH_USERNAME>`
- SSH Password - `export SSH_PASSWORD=<SSH_PASSWORD>`
    - In windows CLI use `set` instead of export
    - In Windows Power Shell use `$Env:` instead of export 

**Create / Update Switch List CSV**
- Add Switch (or Switch Stack) IPs to the switchList.csv (no other information needed)
    - Note this script does **NOT** configure anything on the switch only Show commands on in IOS. All configureation is made in the Meraki Dashboard.
- It is recommeded to backup / migrate switches in batches feel free to create multiple "switchList" Files for this. 
- The CSV will be updated / Mapped with Switch (Switch Stack) Cataylst and Meraki Serial numbers 

Meraki Doc: (Getting started: Cisco Catalyst 9300 Management with Meraki Dashboard
)[https://documentation.meraki.com/MS/Deployment_Guides/Getting_started%3A_Cisco_Catalyst_9300_Management_with_Meraki_Dashboard]

Step 1: Upgrade and Prepare Switches 
- Ensure all switches are on IOS-XE 17.10+ (Recommened 17.12) or Speical Release 17.09.03m3
- Configure / Enable `restconf` on switch
- Configure (in exec mode)`service meraki register ` 
- List all switch (switch stack) IPs on the switchList csv file 

Step 2: Backup IOS Config and Convert to Merkai
- Backup IOS Config and document Switch Details 
- Use the `python backupSWConfig.py -switchlist <switchList.csv> `

Step 3: Configure Meraki Dashboard
- REMEMBER you will need to manually to 
    - Configure SPF / Uplink model ports
    - Add any LACP Config
    - Add any Access Policies / 802.1x Config 
    - Meraki uses MST for Spanning Tree
- `python configureMerakiSW.py -orgid <OrgID> -networkname <MerakiNetworkName> -switchlist <switchList.csv>`

Step 4: Migrate / Convert Switch when ready
- When ready Use the `sevice meraki start` command to factory reset and reimage the C9300 into a Meraki persona.
- Pro Tips
    - Each Switch in a Meraki stack will get an IP address, Start with the switch MGMT VLAN untagged on uplink ports with DHCP enabled. Static IPs can be assigned later
    - Configure LAGs after switch (switch stack is online)
    - Update any missing switch port config (802.1x, tags, STP etc)
 
