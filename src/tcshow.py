#!/bin/python
import os,re
import time
import subprocess
############################

# This is a simple function for extracting useful info from tc -s qdisc show
# Extracted columns include:
# 0   1       2       3           4             5                6                 7        8              9
# idx RootNo. DevName Sent(Bytes) Sent(Packets) Dropped(Packets) Overlimits(Bytes) Requeues Backlog(Bytes) Backlog(Packets) 

############################
entries = []

def col(n, obj = None, clean = lambda e: e):
    """A versatile column extractor.

    col(n, [1,2,3]) => returns the nth value in the list
    col(n, [ [...], [...], ... ] => returns the nth column in this matrix
    col('blah', { ... }) => returns the blah-th value in the dict
    col(n) => partial function, useful in maps
    """
    if obj == None:
        def f(item):
            return clean(item[n])
        return f
    if type(obj) == type([]):
        if len(obj) > 0 and (type(obj[0]) == type([]) or type(obj[0]) == type({})):
            return map(col(n, clean=clean), obj)
    if type(obj) == type([]) or type(obj) == type({}):
        try:
            return clean(obj[n])
        except:
            #print T.colored('col(...): column "%s" not found!' % (n), 'red')
            return None
    # We wouldn't know what to do here, so just return None
    #print T.colored('col(...): column "%s" not found!' % (n), 'red')
    return None

def tcshow (idx,path,delta_t):
#	os.system("tc -s qdisc show")
    mark = []
    tccmd = "tc -s qdisc show"
    result = subprocess.check_output(tccmd,shell=True)
    #print result
#    parse_dev = re.compile(r'qdisc\s*[a-zA-Z_]+\s+[0-9]+:\sdev\s([a-zA-Z0-9-]+)\sroot')
    parse_result = re.compile(r'qdisc\s*[a-zA-Z_]+\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\d]+)b+\s([\d]+)p')
#    matches_dev = parse_dev.findall(result)
    matches_d = parse_result.findall(result)
    num_dev = 0
    for item in matches_d:
    	#if item[1]==path:
    	   if item[1] in path:#find the stats of dev in the path
    	      l= list(item)
    	      l.insert(0,idx)
              l.insert(10,delta_t)
    	      entries.append(l)
    	      if item[1] not in mark: #mark the dev u already found
    	         num_dev+=1 
    	         mark.append(item[1])
    #print col(2,entries)
    #print len(matches_dev)
#    for i in entries:
#	print i
    #print entries[2]
    del mark[:]
    return num_dev
if __name__ == '__main__':
	tcshow(0,['s1-eth2','eth1'],0.50)

