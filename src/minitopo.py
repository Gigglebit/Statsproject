#!/usr/bin/python

"""
"""
import re
import sys
import os

from mininet.log import setLogLevel, debug, info, error,lg
from mininet.net import Mininet
from mininet.link import Intf,TCIntf
from mininet.util import custom,quietRun,irange,dumpNodeConnections
from mininet.cli import CLI
from mininet.node import Node,Controller,RemoteController,OVSKernelSwitch
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink

from subprocess import *
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser
from hwhw import *

parser = ArgumentParser(description = "Pulling Stats Tests")

parser.add_argument('--exp', '-e',
                    dest="exp",
                    action="store",
                    help="Name of the Experiment",
                    required=True)

parser.add_argument('--btnSpeed', '-b',
                    dest="btn",
                    action="store",
                    help="Bottleneck link speed",
                    required=True)

parser.add_argument('--hs_bw', '-HS',
                    dest="hs_bw",
                    type=float,
                    action="store",
                    help="Bandwidth between hosts and switchs",
                    required=True)

parser.add_argument('--delay',
                    dest="delay",
                    type=float,
                    help="Delay in milliseconds of host links",
                    default=10)

parser.add_argument('--maxq',
                    dest="maxq",
                    action="store",
                    help="Max buffer size of network interface in packets",
                    default=1000)

parser.add_argument('--intf1',
                    dest="intf1",
                    type=str,
                    action="store",
                    help="Real Interface",
                    required=True)

parser.add_argument('--intf2',
                    dest="intf2",
                    type=str,
                    action="store",
                    help="Real Interface",
                    required=True)

args = parser.parse_args()

class SimpleTopo(Topo):

   def __init__(self, k=2):
       super(SimpleTopo, self).__init__()
       self.k = k
       dhcp = self.addHost('dhcp')
       lastSwitch = None
       for i in irange(1, k):
           host = self.addHost('h%s' % i)
           switch = self.addSwitch('s%s' % i)
           # 10 Mbps, 5ms delay, 1% loss, 1000 packet queue
           self.addLink( host, switch, bw=int(args.hs_bw), max_queue_size=int(args.maxq), use_htb=True)
           if lastSwitch:
               self.addLink(switch, lastSwitch, bw=int(args.btn), max_queue_size=int(args.maxq), use_htb=True)
           lastSwitch = switch
       self.addLink(dhcp, lastSwitch, bw=int(args.hs_bw), max_queue_size=int(args.maxq), use_htb=True)
       
topos = { 'mytopo': ( lambda: SimpleTopo() ) }

def Test():
   "Create network and run simple performance test"
   topo = SimpleTopo(k=2)
   net = Mininet(topo=topo,
                 host=CPULimitedHost, link=TCLink)
   s1 = net.getNodeByName('s1')
   s2 = net.getNodeByName('s2')
   addRealIntf(net,args.intf1,s1)
   addRealIntf(net,args.intf2,s2)
   net.start()
   print "Dumping host connections"
   dumpNodeConnections(net.hosts)
 
   net.pingAll()
   #h1 = net.getNodeByName('h1')
   dhcp = net.getNodeByName('dhcp')
   out = dhcp.cmd('sudo dhcpd')
   print "DHCPD = "+ out
   #h1.cmd("bash tc_cmd_diff.sh h1-eth0")
   #h1.cmd("tc -s show dev h1-eth0")
  # h2.cmd('iperf -s -w 16m -p 5001 -i 1 > iperf-recv.txt &')
   #h2.cmd('iperf -s -p %s -i 1 > iperf_server_TCP.txt &' % 5001)
#               (CUSTOM_IPERF_PATH, 5001, args.dir))
   #monitoring the network
  #monitor = Process(target=monitor_qlen,
                     #args=("%s"%args.iface,float(args.sampleR),int(args.nQ), "%s_%s"% (args.exp,args.out)))   
       

              
   #start mininet CLI
   CLI(net)
   #terminate

   os.system('killall -9 iperf' )
   net.hosts[0].cmd('killall -9 dhcpd')
   net.stop()

   Popen("killall -9 cat", shell=True).wait()

if __name__ == '__main__':
   setLogLevel('info')
   Test()
