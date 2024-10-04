#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
#from mininet.node import OVSKernelSwitch, UserSwitch
#from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import time 

from eBPFSwitch import eBPFSwitch, eBPFHost

def smartGridSimNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='1.0.0.0/8',
                   host = eBPFHost, 
                   switch = eBPFSwitch)

    info( '\n*** ************************************* *** \n' )
    info( '*** Starting SGSim - BPFabric Orchestration *** \n' )
    info( '*** Topology: 1xDPS + 2xDSS + Control Center \n' )
    info( '*** Version: 240619 \n' )
    info( '*** Author: filip.holik@glasgow.ac.uk  \n' )
    info( '*** ************************************* *** \n' )
    info( '*** Adding controller\n' )
    #c0=net.addController(controller=None)  
    #net.addController(name='c0',
    #controller=OVSController,
    #protocol='tcp',
    #port=6633)

    switchPath = "../../BPFabric/softswitch/softswitch"; 
    #switchType = OVSKernelSwitch; 

    info( '*** Starting networking devices\n')
    DSS1GW = net.addSwitch('DSS1GW', dpid=1, switch_path=switchPath)     
    DSS2GW = net.addSwitch('DSS2GW', dpid=2, switch_path=switchPath)  
    WANR1 = net.addSwitch('WANR1', dpid=3,switch_path=switchPath) 
    WANR2 = net.addSwitch('WANR2', dpid=4, switch_path=switchPath) 
    CONTROLSW = net.addSwitch('CONTROLSW', dpid=5, switch_path=switchPath)  
    DPSGW = net.addSwitch('DPSGW', dpid=6, switch_path=switchPath) 
    DPSRS = net.addSwitch('DPSRS', dpid=7, switch_path=switchPath) 
    DPSHV = net.addSwitch('DPSHV', dpid=8, switch_path=switchPath) 
    DPSMV = net.addSwitch('DPSMV', dpid=9, switch_path=switchPath) 

    info( '*** Starting external connection\n')
    #DSS1ASW = net.addSwitch('DSS1ASW', dpid=10, switch_path=switchPath) #,failMode='standalone') 
    #DSS2ASW = net.addSwitch('DSS2ASW', dpid=11, switch_path=switchPath) #,failMode='standalone') 
    #Intf( 'enp0s3', node=DSS1ASW )
    #Intf( 'enp0s8', node=DSS2ASW )
    #Intf( 'enp0s9', node=DPSHV )
    #Intf( 'enp0s10', node=DPSGW )

    info( '*** Starting hosts \n')
    DSS1RTU = net.addHost('DSS1RTU', cls=eBPFHost, ip='1.1.1.1', defaultRoute='1.1.10.10',mac='00:00:00:00:00:06')
    DSS2RTU = net.addHost('DSS2RTU', cls=eBPFHost, ip='1.1.2.1', defaultRoute='1.1.10.10',mac='00:00:00:00:00:07')
    CONTROL = net.addHost('CONTROL', cls=eBPFHost, ip='1.1.10.10', defaultRoute='1.1.1.1',mac='00:00:00:00:00:08')
    IED1 = net.addHost('IED1', cls=eBPFHost, ip='1.1.3.1', defaultRoute='1.1.10.10',mac='b4:b1:5a:00:00:01')
    IED2 = net.addHost('IED2', cls=eBPFHost, ip='1.1.3.2', defaultRoute='1.1.10.10',mac='00:00:00:00:00:02')
    IED3 = net.addHost('IED3', cls=eBPFHost, ip='1.1.3.3', defaultRoute='1.1.10.10',mac='00:00:00:00:00:03')
    IED4 = net.addHost('IED4', cls=eBPFHost, ip='1.1.3.4', defaultRoute='1.1.10.10',mac='30:B2:16:00:00:04')
    DPSHMI = net.addHost('DPSHMI', cls=eBPFHost, ip='1.1.3.10', defaultRoute='1.1.10.10',mac='00:00:00:00:00:05')
    IDS = net.addHost('IDS', cls=eBPFHost, ip='1.1.1.8', defaultRoute='1.1.10.10',mac='00:00:00:00:00:88')
    ATTACKER = net.addHost('ATTACKER', cls=eBPFHost, ip='1.1.3.66', defaultRoute='1.1.10.10',mac='00:00:00:00:00:66')
    
    info( '*** Setting link parameters\n')
    #WAN1 = {'bw':1000,'delay':'20ms','loss':1,'jitter':'10ms'} 
    #GBPS = {'delay':'18ms'} 
    MBPS = {'bw':10} 

    info( '*** Adding links\n')
    net.addLink(WANR2, CONTROLSW)
    net.addLink(WANR1, CONTROLSW)
    net.addLink(CONTROLSW, CONTROL)
    net.addLink(WANR1, DSS1GW, cls=TCLink , **MBPS)
    net.addLink(WANR2, DSS2GW, cls=TCLink , **MBPS)

    net.addLink(DPSGW, CONTROLSW)
    net.addLink(DPSGW, DPSRS)
    net.addLink(DPSRS, DPSHV)
    net.addLink(DPSRS, DPSMV)
    net.addLink(IED1, DPSHV)
    net.addLink(IED2, DPSHV)
    net.addLink(IED3, DPSMV)
    net.addLink(IED4, DPSMV)
    net.addLink(DPSHMI, DPSRS)

    net.addLink(DSS1GW, IDS)
    net.addLink(ATTACKER, DPSHV)

    info( '*** Adding redundant links\n')
    #net.addLink(WANR2, DSS1GW, cls=TCLink , **GBPS)
    #net.addLink(WANR1, DSS2GW, cls=TCLink , **GBPS)
    net.addLink(DSS1GW, DSS1RTU)
    net.addLink(DSS2GW, DSS2RTU)

    info( '*** Adding links for external connections \n')
    #net.addLink(DSS1RTU, DSS1ASW)
    #net.addLink(DSS1ASW, DSS1GW)
    #net.addLink(DSS2RTU, DSS2ASW)
    #net.addLink(DSS2ASW, DSS2GW)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting networking devices\n')
    net.get('DSS1GW').start([])
    net.get('DSS2GW').start([])
    net.get('WANR1').start([])
    net.get('WANR2').start([])
    net.get('CONTROLSW').start([])
    #net.get('DSS1ASW').start([])
    #net.get('DSS2ASW').start([])
    net.get('DPSGW').start([])
    net.get('DPSRS').start([])
    net.get('DPSHV').start([])
    net.get('DPSMV').start([])

    info( '*** Preparing custom scripts \n')
    CLI.do_sgsim_startcom_104 = sgsim_startcom_104
    CLI.do_sgsim_startcom_goose = sgsim_startcom_goose
    CLI.do_sgsim_startcom_sglab_goose = sgsim_startcom_sglab_goose
    CLI.do_sgsim_startcom_sv = sgsim_startcom_sv
    CLI.do_sgsim_startperfmon = sgsim_startperfmon
    CLI.do_sgsim_attackmirror = sgsim_attackmirror
    CLI.do_sgsim_attack_goose_fdi = sgsim_attack_goose_fdi
    CLI.do_sgsim_attack_dos = sgsim_attack_dos
    info( '*** Smart Grid Simulation Model Started *** \n' )
    CLI(net)

    net.stop()

def sgsim_startcom_goose(self, line):
    "Starts the GOOSE communication in the primary substation." 
    net = self.mn  
    info('Inserting rules for DPSGW switch... \n')
    net.get('DPSGW').cmdPrint('ovs-ofctl add-flow DPSGW dl_type=0x88b8,action=DROP')     # Simulation of GOOSE multicast 
    info('Starting GOOSE communication... \n')    
    net.get('IED1').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "IED1-GOOSE" -e "cd ../comlib_dps/sgdevices/IED_GOOSE/;./ied_goose IED1-eth0;bash"&') 
    time.sleep(0.5)
    net.get('IED4').cmdPrint('xterm -geometry 90x30+30+30 -fa "Monospace" -fs 12 -T "IED4-GOOSE" -e "cd ../comlib_dps/sgdevices/IED_GOOSE/;./ied_goose IED4-eth0;bash"&') 
    time.sleep(0.5)
    net.get('DPSHMI').cmdPrint('xterm -geometry 90x30+50+50 -fa "Monospace" -fs 12 -T "DPSHMI-GOOSE-1" -e "cd ../comlib_dps/sgdevices/DPSHMI_GOOSE/;./dpshmi;bash"&') 
    time.sleep(0.5)
    net.get('DPSHMI').cmdPrint('xterm -geometry 90x30+70+70 -fa "Monospace" -fs 12 -T "DPSHMI-GOOSE-4" -e "cd ../comlib_dps/sgdevices/DPSHMI_GOOSE/;./dpshmi;bash"&') 

def sgsim_startcom_sglab_goose(self, line):
    "Starts the GOOSE communication according to the SG LAB data." 
    net = self.mn  
    info('Inserting rules for DPSGW switch... \n')
    net.get('DPSGW').cmdPrint('ovs-ofctl add-flow DPSGW dl_type=0x88b8,action=DROP')     # Simulation of GOOSE multicast 
    info('Starting GOOSE communication... \n')    
    net.get('IED1').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "IED1-GOOSE" -e "cd ../comlib_dps/sgdevices/IED_GOOSE/;./ied_goose_sglab IED1-eth0;bash"&') 
    time.sleep(0.5)
    net.get('DPSHMI').cmdPrint('xterm -geometry 90x30+50+50 -fa "Monospace" -fs 12 -T "DPSHMI-GOOSE-1" -e "cd ../comlib_dps/sgdevices/DPSHMI_GOOSE/;./dpshmi;bash"&') 

def sgsim_attack_goose_fdi(self, line):
    "Starts the False Data Injection attack on GOOSE communication." 
    net = self.mn  
    info('Starting FDI attack... \n')    
    net.get('ATTACKER').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "ATTACKER-FDI" -e "cd ../comlib_dps/sgdevices/ATTACKER/;./fdi_goose ATTACKER-eth0;bash"&') 
    time.sleep(0.5)
    net.get('DPSHMI').cmdPrint('xterm -geometry 90x30+50+50 -fa "Monospace" -fs 12 -T "DPSHMI-GOOSE" -e "cd ../comlib_dps/sgdevices/DPSHMI_GOOSE/;./dpshmi;bash"&') 

def sgsim_attack_dos(self, line):
    "Starts the DoS attack from DSS1RTU on the control center." 
    net = self.mn  
    info('Starting DoS attack... \n')    
    net.get('DSS1RTU').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "ATTACKER-DOS" -e "sudo hping3 -S --flood 1.1.10.10;bash"&') 

def sgsim_startcom_sv(self, line):
    "Starts the SV communication in the primary substation." 
    net = self.mn  
    info('Inserting rules for DPSGW switch... \n')
    net.get('DPSGW').cmdPrint('ovs-ofctl add-flow DPSGW dl_type=0x88ba,action=DROP')     # Simulation of SV multicast 
    info('Starting SV communication... \n')    
    net.get('IED2').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "IED2-SV" -e "cd ../comlib_dps/sgdevices/IED_SV/;./ied_sv IED2-eth0;bash"&') 
    time.sleep(0.5)
    net.get('IED3').cmdPrint('xterm -geometry 90x30+30+30 -fa "Monospace" -fs 12 -T "IED3-SV" -e "cd ../comlib_dps/sgdevices/IED_SV/;./ied_sv IED3-eth0;bash"&') 
    time.sleep(0.5)
    net.get('DPSHMI').cmdPrint('xterm -geometry 90x30+50+50 -fa "Monospace" -fs 12 -T "DPSHMI-SV-2" -e "cd ../comlib_dps/sgdevices/DPSHMI_SV/;./dpshmi_sv 2;bash"&') 
    time.sleep(0.5)
    net.get('DPSHMI').cmdPrint('xterm -geometry 90x30+70+70 -fa "Monospace" -fs 12 -T "DPSHMI-SV-3" -e "cd ../comlib_dps/sgdevices/DPSHMI_SV/;./dpshmi_sv 3;bash"&') 
    time.sleep(0.5)

def sgsim_startcom_104(self, line):
    "Starts the IEC104 communication (periodical and read requests) for both secondary substations." 
    net = self.mn   
    info('Starting IEC104 communication... \n')    
    info('Starting DSS1RTU communication... \n')    
    net.get('DSS1RTU').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "DSS1RTU" -e "cd ../comlib_dss/sgdevices/RTU/;./rtu;bash"&') 
    time.sleep(0.5)
    info('Starting DSS2RTU communication... \n')    
    net.get('DSS2RTU').cmdPrint('xterm -geometry 90x30+30+30 -fa "Monospace" -fs 12 -T "DSS2RTU" -e "cd ../comlib_dss/sgdevices/RTU/;./rtu;bash"&') 
    time.sleep(0.5)
    info('Starting CONTROL communication with DSS1... \n')    
    net.get('CONTROL').cmdPrint('xterm -geometry 90x30+50+50 -fa "Monospace" -fs 12 -T "CONTROL - DSS1 Monitoring" -e "cd ../comlib_dss/sgdevices/CONTROL/;sleep 1;./control 1.1.1.1;bash"&') 
    time.sleep(0.5)
    info('Starting CONTROL communication with DSS2... \n')  
    net.get('CONTROL').cmdPrint('xterm -geometry 90x30+70+70 -fa "Monospace" -fs 12 -T "CONTROL - DSS2 Monitoring" -e "cd ../comlib_dss/sgdevices/CONTROL/;sleep 1;./control 1.1.2.1;bash"&')
    info('IEC104 communication started... \n(Please close all the opened windows before exiting the Mininet.)  \n')   

def sgsim_startperfmon(self, line):
    "Starts the IEC104 communication (periodical and read requests) with performance monitoring." 
    net = self.mn   
    info('Starting IEC104 communication with performance monitoring... \n')    
    info('Starting DSS1RTU communication... \n')    
    net.get('DSS1RTU').cmdPrint('xterm -geometry 90x30+10+10 -fa "Monospace" -fs 12 -T "DSS1RTU" -e "cd ../comlib_dss/sgdevices/PERFSEND/;./perfsend;bash"&') 
    time.sleep(0.5)
    info('Starting DSS2RTU communication... \n')    
    net.get('DSS2RTU').cmdPrint('xterm -geometry 90x30+30+30 -fa "Monospace" -fs 12 -T "DSS2RTU" -e "cd ../comlib_dss/sgdevices/PERFSEND/;./perfsend;bash"&') 
    time.sleep(0.5)
    info('Starting CONTROL communication with DSS1... \n')    
    net.get('CONTROL').cmdPrint('xterm -geometry 90x30+50+50 -fa "Monospace" -fs 12 -T "CONTROL - DSS1 Monitoring" -e "cd ../comlib_dss/sgdevices/PERFMON/;sleep 1;./perfmon 1.1.1.1;bash"&') 
    time.sleep(0.5)
    info('Starting CONTROL communication with DSS2... \n')  
    net.get('CONTROL').cmdPrint('xterm -geometry 90x30+70+70 -fa "Monospace" -fs 12 -T "CONTROL - DSS2 Monitoring" -e "cd ../comlib_dss/sgdevices/PERFMON/;sleep 1;./perfmon 1.1.2.1;bash"&')
    info('IEC104 communication with performance monitoring started... \n(Please close all the opened windows before exiting the Mininet.)  \n')   

def sgsim_attackmirror(self, line):
    "Makes DSS ASW devices to mirror traffic to external connections. "
    net = self.mn   
    info('Inserting rules for DSS1 switch... \n')    
    net.get('DSS1ASW').cmdPrint('ovs-ofctl add-flow DSS1ASW in_port:2,action=1,3; ovs-ofctl add-flow DSS1ASW in_port:3,action=1,2') 
    info('Inserting rules for DSS2 switch... \n')    
    net.get('DSS2ASW').cmdPrint('ovs-ofctl add-flow DSS2ASW in_port:2,action=1,3; ovs-ofctl add-flow DSS2ASW in_port:3,action=1,2') 

if __name__ == '__main__':
    setLogLevel( 'info' )
    smartGridSimNetwork()





