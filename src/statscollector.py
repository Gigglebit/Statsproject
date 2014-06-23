from bottle import route, run
import subprocess 
import ntplib
from time import ctime
from json import dumps
from agent import *

#jpip_stats = []

@route('/hello')
def hello():
    return "Hello World!"

#switch_list = ["10.0.0.1:9999","10.0.0.2:9998","10.0.0.3:9997"]

@route("/stats/<start_ip>/<end_ip>/<earliest_idx>/<num_entries>",method='GET')
def get_path_stats(start_ip, end_ip,earliest_idx,num_entries):
   #net = []
   path = find_path(start_ip, end_ip)
#   for iface in path:
   #jpip_stats = []
   start_monitor(path)
   #get_port_stats(path,earliest_idx,num_entries)   
   #port_stats = get_port_stats(path[1])
   #net.append(stats)
#
   jpip_stats=return_stats(path,int(earliest_idx),int(num_entries))
   #print jpip_stats
   return dumps(jpip_stats)
   #return jpip_stats

#def get_port_stats(path,e_idx,num_entries):
   # stats = []
   # Get the local elements
   # t = get_time()
   # bw = get_bandwidth(path)
   # delay = get_delay(path)
   # save to the dictionary
   # stats.append(t)
   # stats.append(bw)
   # stats.append(delay)
   #stats["time"] = t
   #stats["bw"] = bw
   #stats["delay"] = delay
#   start_monitor(["eth0","eth1"],0,0)
#   return 

# #def get_bandwidth_by_link(links):

# #global switch_list

# #for item in switch_list:
# #    get_bandwidth_by_port(item[portname])

# def get_bandwidth(path):
#    return "5" Mbps
# def get_delay(links):
#    return "2" #ms
# def get_time():
#    c = ntplib.NTPClient()
#    response = c.request('europe.pool.ntp.org', version=3)
#    return ctime(response.tx_time)

def find_path(a_ip,b_ip):
   retVal = ["s1-eth2","eth1"]

# STATICALY DEFINE LINKS IN HERE.

   return retVal

run(host='149.171.37.108', port=8080, debug=True)
