from bottle import route, run
import subprocess 
import ntplib
from time import ctime
from json import dumps
from agent import *

#jpip_stats = []
max_bw = []
@route('/hello')
def hello():
    return "Hello World!"

#switch_list = ["10.0.0.1:9999","10.0.0.2:9998","10.0.0.3:9997"]

@route("/stats/<start_ip>/<end_ip>/<earliest_idx>/<num_entries>",method='GET')
def get_path_stats(start_ip, end_ip,earliest_idx,num_entries):
   path = find_path(start_ip, end_ip)
   print path
   start_monitor(path)
   jpip_stats=return_stats(path,int(earliest_idx),int(num_entries))
   return dumps(jpip_stats)

def find_path(a_ip,b_ip):
   global max_bw
   if a_ip == "1":
   	retVal = ["s1-eth2","eth1"]
	return retVal
   if b_ip == "1":
   	retVal = ["s2-eth2","eth0"]
	return retVal
# STATICALY DEFINE LINKS IN HERE.


run(server='paste',host='10.0.0.254', port=8080, debug=True)
#run(host='10.0.2.15', port=8080, debug=True)
