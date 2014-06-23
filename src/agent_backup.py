#!/bin/python
import time
#from time import sleep, time, clock
from subprocess import *
import re
from multiprocessing import Process, Manager
import threading
from tcshow import *

jpip_stats=[]
MAX_BUF=100
get_Stat=True
monitor_run = False
class Timer(threading.Thread):
	"""
	Timing the sampling rate
	"""
	def __init__(self,seconds):
		super(Timer, self).__init__()
		self.runTime = seconds
		self.keeprunning = 1
		#threading.Thread.__init__(self)
	def run(self):
		try:
			while self.keeprunning:
				start = time.time()
				time.sleep(self.runTime)
				end = time.time()
				#print end-start
				global get_Stat
				get_Stat = True
			#print get_Stat
		except KeyboardInterrupt:
				print "stoptimer"
				stop()
	def stop(self):			
		self.keeprunning = 0


def cal_bw_delay(entries_range,entries_start,idx,delta_t,num_dev):
	'''
	This function append reverse order entries into jpip_stats
	Tell me the range of entries
	and tell me the reversed order starting point
	for example, to generate the following output, entries_range = 4, entries_start = 100 
	100,t,bw
	 99,t,bw
	 98,t,bw
	 97,t,bw
	since our window only has 100 entries, 
	when the idx go above 100 always set entries_start=MAX_BUF 
	otherwise entries_start=idx
	'''
	for i in xrange(entries_range):
		l = []
		b = []
		delay_sum = 0
		for j in xrange(num_dev):
			delta_sentB = int(col(3,entries[(entries_start-i)*num_dev+j]))-int(col(3,entries[(entries_start-i-1)*num_dev+j]))
			bw = float(delta_sentB)/float(delta_t)
			b.append("%.3f"%bw)
			if bw != 0: #data in transmission, let me know the average delay in a time interval 
				delay = (int(col(8,entries[(entries_start-i)*num_dev+j]))+int(col(8,entries[(entries_start-i-1)*num_dev+j])))/(2*bw)
			else:
				delay = 0
			delay_sum+=delay			
		l.append(idx-i)
		l.append("%.3f"%delta_t)
		l.append(max(b))
		l.append("%.3f"%delay_sum)
		jpip_stats.append(l)

def resolve_idx(path,idx,earliest_idx,num_entries,delta_t,num_dev):
	del jpip_stats[:]
	if num_entries >= MAX_BUF or num_entries >= idx or earliest_idx > idx or num_entries < 0 or earliest_idx < 0:
		jpip_stats.append(" ") #if anything is outbound return nothing
		return	

	if num_entries==0 and earliest_idx ==0:
		if idx-MAX_BUF>=0:#when the moving window has 100 entries
			cal_bw_delay(MAX_BUF,MAX_BUF,idx,delta_t,num_dev)
			# for i in xrange(MAX_BUF):
			# 	l = []
			# 	b = []
			# 	delay_sum = 0
			# 	for j in xrange(num_dev):
			# 		delta_sentB = int(col(3,entries[(MAX_BUF-i)*num_dev+j]))-int(col(3,entries[(MAX_BUF-i-1)*num_dev+j]))
			# 		bw = float(delta_sentB)/float(delta_t)
			# 		b.append("%.3f"%bw)
			# 		if bw != 0: #data in transmission, let me know the average delay in a time interval 
			# 			delay = (int(col(8,entries[(MAX_BUF-i)*num_dev+j]))+int(col(8,entries[(MAX_BUF-i-1)*num_dev+j])))/(2*bw)
			# 		else:
			# 			delay = 0
			# 		delay_sum+=delay
					
			# 	l.append(idx-i)
			# 	l.append("%.3f"%delta_t)
			# 	l.append(max(b))
			# 	l.append("%.3f"%delay_sum)
			# 	jpip_stats.append(l)				
		else:
			cal_bw_delay(idx,idx,idx,delta_t,num_dev)
			# for i in xrange(idx):
			# 	l = []
			# 	b = []
			# 	delay_sum = 0
			# 	for j in xrange(num_dev):
			# 		delta_sentB = int(col(3,entries[(idx-i)*num_dev+j]))-int(col(3,entries[(idx-i-1)*num_dev+j]))
			# 		bw = float(delta_sentB)/float(delta_t)
			# 		b.append("%.3f"%bw)
			# 		if bw != 0: #data in transmission, let me know the average delay in a time interval 
			# 			delay = (int(col(8,entries[(idx-i)*num_dev+j]))+int(col(8,entries[(idx-i-1)*num_dev+j])))/(2*bw)
			# 		else:
			# 			delay = 0
			# 		delay_sum+=delay
					
			# 	l.append(idx-i)
			# 	l.append("%.3f"%delta_t)
			# 	l.append(max(b))
			# 	l.append("%.3f"%delay_sum)
			# 		#print "dev eth%d "%j + "%d Bps"%bw 
			# 	jpip_stats.append(l)
	elif num_entries!=0 and earliest_idx ==0:
		if idx-MAX_BUF>=0:
			cal_bw_delay(num_entries,MAX_BUF,idx,delta_t,num_dev)
		else:
			cal_bw_delay(num_entries,idx,idx,delta_t,num_dev)
	elif num_entries==0 and earliest_idx !=0:
		if idx-MAX_BUF>=0:
			if earliest_idx < idx-MAX_BUF:
				cal_bw_delay(MAX_BUF,MAX_BUF,idx,delta_t,num_dev)
			else:
				cal_bw_delay(idx-earliest_idx,MAX_BUF,idx,delta_t,num_dev)
		else:
			cal_bw_delay(idx-earliest_idx,idx,idx,delta_t,num_dev)
	else:
		if idx-MAX_BUF>=0:
			if idx-num_entries < earliest_idx:
				cal_bw_delay(idx-earliest_idx,MAX_BUF,idx,delta_t,num_dev)
			else:
				cal_bw_delay(num_entries,MAX_BUF,idx,delta_t,num_dev)
		else:
			if idx-num_entries < earliest_idx:
				cal_bw_delay(idx-earliest_idx,idx,idx,delta_t,num_dev)
			else:
				cal_bw_delay(num_entries,idx,idx,delta_t,num_dev)

# def monitor_stats(path,earliest_idx,num_entries,interval_sec = 1):
# 	try:

# 		num_dev = 0
# 		idx=0
# 		delta_t = 0
# 		global get_Stat
# 		timer = Timer(interval_sec)
# 		timer.start()
# 		while 1:
# 			if get_Stat:
# 				t= time.time()
# 				num_dev=tcshow(idx,path) # tell me the stats along the path 
# 				get_Stat=False
# 				if num_dev!=0:
# 					if idx > 0: # give me time interval
# 						delta_t = float(t) - float(prev_t)
# 						resolve_idx(path,idx,earliest_idx,num_entries,delta_t,num_dev)

# 					#print "index: %d "%j + "Bandwidth: %f in Bps"%bw + " and queuing delay in %d s" %delay_sum
# 				if idx >= MAX_BUF: #ensure max 100 entries
# 					del entries[0:num_dev] #keep window size to be 100
# 				idx+=1
# 				prev_t = t

			#sleep(interval_sec) #sampling speed set for interval
class monitor_stats(threading.Thread):
	"""
	Timing the sampling rate
	"""
	def __init__(self,path,earliest_idx,num_entries):
		super(monitor_stats, self).__init__()
		#self.runTime = interval_sec
		self.path = path
		self.earliest_idx = earliest_idx
		self.num_entries = num_entries
		self.keeprunning = 1
		#threading.Thread.__init__(self)
	def run(self):
		try:
			num_dev = 0
	 		idx=0
	 		delta_t = 0
 			global get_Stat
			while self.keeprunning:
				if get_Stat:
					t= time.time()
					num_dev=tcshow(idx,self.path) # tell me the stats along the path 
					get_Stat=False
					if num_dev!=0:
						if idx > 0: # give me time interval
							delta_t = float(t) - float(prev_t)
							resolve_idx(self.path,idx,self.earliest_idx,self.num_entries,delta_t,num_dev)

						#print "index: %d "%j + "Bandwidth: %f in Bps"%bw + " and queuing delay in %d s" %delay_sum
					if idx >= MAX_BUF: #ensure max 100 entries
						del entries[0:num_dev] #keep window size to be 100
					idx+=1
					prev_t = t
		except KeyboardInterrupt:
				print "stoptimer"
				stop()
	def stop(self):			
		self.keeprunning = 0
			
def start_monitor(path,earliest_idx,num_entries):
	manager =Manager()
	manager.list()
	global monitor_run
	if not monitor_run:
		monitor_run = True
		p = Process(target=monitor_stats,args=(path,earliest_idx,num_entries,0.05))
		p.start()
		#p.join()
		#monitor_stats(path,earliest_idx,num_entries,0.05)
	#first URL return nothing, but start monitoring
	return 0

def end_monitor():
	#no request after awhile 60s? stop the monitor process
	return 0

if __name__ == '__main__':
	try:
		timer = Timer(0.05)
		timer.start()
		path = ["eth0","eth1"]
		m =monitor_stats(path,60,80)
		m.start()
	except KeyboardInterrupt:
		timr.stop()
		m.stop()