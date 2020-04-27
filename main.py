#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# howto INSTALL:
# pip install -r requirements.txt

import configparser 
import re
import json
import logging as log
from datetime import date

from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoAuthenticationException
from netmiko.ssh_exception import NetMikoTimeoutException

log.basicConfig(level=log.INFO)

log.info('DEVNET MARATHON HOME WORK demo.')
config = configparser.ConfigParser()
log.info("Try read config file...")
config.read('config.conf')
report = []

for Host in  config.options('hosts'):
    log.info("Proceed homework for host: %s method: %s ",Host,config['hosts'][Host])
    if(config['hosts'][Host] == "SSH"):
        device = {
            'device_type': 'cisco_ios',
            'ip': Host,
            'username': config[Host]['Username'],
            'password': config[Host]['Password'],
            'port': config[Host]['SSH Port']
          }
        ver=img=npe=cdp=clock=""  
        
        try:
            with ConnectHandler(**device) as ssh:
                ssh.enable()
                # 1 Save running-config to local file
                runningConfig = ssh.send_command("show running-config")
                
                today = date.today()
                file_name = Host + '_' + today.strftime("%Y-%m-%d") + ".txt"
                with open(file_name, 'w') as file:
                    log.info("Save host %s  config to %s ",Host,file_name)
                    file.write(runningConfig)
                #Done

                # 2 Check CDP 
                Cdp = ssh.send_command('show cdp neighb')
                c = re.search(r'CDP is not enabled',Cdp)
                if c:
                    cdp="CDP is OFF"
                else:
                    regex = re.compile(r"(?P<r_dev>\w+)  +(?P<l_intf>\S+ \S+)" 
                                       r"  +\d+  +[\w ]+  +\S+ +(?P<r_intf>\S+ \S+)"  )
                    nbr_count = 0
                    for match in regex.finditer(Cdp):
                        nbr_count += 1
                    cdp="CDP is ON, %d peers" % nbr_count
                 

                log.info("Host %s cdp %s",Host,cdp)
                #Done
                
                
                # 3 Collect version data
                Version =  ssh.send_command('show version')
                m = re.search(r'^Cisco IOS.+,.+\((.+)\), Version (.+),.+$', Version, flags=re.MULTILINE)
                if m:
                    ver =  m.group(2)
                    img = m.group(1)
                    n = re.search(r'npe', img)
                    if n:
                        npe = 'NPE'
                    else:
                        npe = 'PE'
                    
                else:
                     m = re.search(r'^Cisco.+\((.+)\) Software$', Version, flags=re.MULTILINE)
                     if m:
                         img = m.group(1)
                         if ( img == 'NX-OS' ):
                             v = re.search(r'NXOS:\s+version\s+(.+)\s*$',Version,flags=re.MULTILINE)
                             if v:
                                 ver = v.group(1)
                             if re.search(r'npe',Version,flags=re.MULTILINE):
                                 npe = 'NPE'
                             else:
                                 npe = 'PE'
                
                log.info("Host %s ver: %s  img: %s  %s", Host,ver,img, npe)       

                            
                        
                             



                     
                #Done

                # 4 Timezone & Ntp settings
                
                PingNtp = ssh.send_command('ping ' + config['ntp settings']['server ip'])
                if re.search(r'Success rate is 100 percent', PingNtp, flags=re.MULTILINE):
                    NtpSet = ssh.send_config_set([ 'clock timezone ' + config['ntp settings']['timezone'], 
                                                  'ntp server ' + config['ntp settings']['server ip']                                   
                    ])
                    ssh.send_command('wr')
                    NtpStatus =  ssh.send_command('show ntp status')
                    if re.search(r'Clock is synchronized', NtpStatus, flags=re.MULTILINE):
                        clock = 'Clock is sync'
                    else:
                        clock = 'Clock is not sync'
                else:
                    clock = 'Ntp is unavailable'
                log.info("Host %s clock %s",Host,clock)
                #Done
                ssh.disconnect()

                #Add line to report
                report.append('|'.join([Host,img,ver,npe,cdp,clock]))
        except (NetMikoAuthenticationException, NetMikoTimeoutException) as e:
            log.error("Connection error: " + str(e))
        
        
print ("\nReport:")
print ('\n'.join(report))

                      
        
            








