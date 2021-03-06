#!/bin/python
import time
#from time import sleep, time, clock
import threading
import Queue
from Queue import *
from thread import *
from subprocess import *
import re
from multiprocessing import Process, Manager
from tcshow import *

#shared Queue for multithreads
q=Queue(maxsize=3)
#back_q= Queue(maxsize=1)

#output
'''
The output jpip_stats is a summarised list of the entire path. 
Each entry includes [index,time,available bandwidth,delay]
available bandwidth is calculated based on the min{bw on the path} e.g. min{bw@eth0,bw@eth1}
delay is added up from all 
Based on the requests of earliest_idx and num_entries, it generates different length of entries
The logic is demonstrated in function: resolve_idx
'''
jpip_stats=[]

#length of the buffer
MAX_BUF=100

#flags
get_Stat=True
monitor_run = False
called = False

#track of threads
threads=[]

#link capacity 
#max_bw = [640000,12500000]#5Mbps/100Mbps
max_bw = [1280000,640000]
#sampling timer, sampling at every 50ms
class Timer(threading.Thread):
	"""
	Timing the sampling rate 50ms
	Every 50ms it updates the global flag get_Stat to tell monthread time to pull tc
	"""
	def __init__(self,seconds):
		super(Timer, self).__init__()
		self.runTime = seconds
		self.keeprunning = 1
	def run(self):
		try:
			while self.keeprunning:
				time.sleep(self.runTime)
				global get_Stat
				get_Stat = True
		except KeyboardInterrupt:
				print "stoptimer"
				self.stop()
	def stop(self):			
		self.keeprunning = 0


def cal_bw_delay(entries_range,entries_start,idx,delta_t,num_dev):
	'''
	This function append reverse-ordered entries into the output jpip_stats[]. e.g. the top entry is the latest
	Tell me the range of entries
	and tell me the reversed order starting point
	for example, to generate the following output, entries_range = 4, entries_start = 100 
	100,t,bw
	 99,t,bw
	 98,t,bw
	 97,t,bw
	since our window only has 100 entries, 
	when the idx go above 100, always set entries_start=MAX_BUF,
	otherwise entries_start=idx
	entries[] is a global variable defined in tcshow.py
	'''
	global max_bw
	for i in xrange(entries_range):
		l = []
		b = []
		delay_sum = 0
		for j in xrange(num_dev):
			delta_sentB = int(col(3,entries[(entries_start-i)*num_dev+j]))-int(col(3,entries[(entries_start-i-1)*num_dev+j]))
			delta_sentP = int(col(4,entries[(entries_start-i)*num_dev+j]))-int(col(4,entries[(entries_start-i-1)*num_dev+j]))
			bw = float(delta_sentB)/float(delta_t[(entries_start-i)*num_dev]) #Bytes/sec
			#bwp = float(delta_sentP)/float(delta_t[(entries_start-i)*num_dev]) #Pkts/sec
			#print j 
			#print max_bw
			avail_bw = float(max_bw[j])-bw
			if avail_bw > 0:
				b.append(avail_bw)
			else:
				b.append(0.0)
			#if bwp != 0: #data in transmission, let me know the instantaneous delay in a time interval 
				#delay = (int(col(8,entries[(entries_start-i)*num_dev+j]))+int(col(8,entries[(entries_start-i-1)*num_dev+j])))/(2*bw)
				#delay = (int(col(9,entries[(entries_start-i)*num_dev+j]))+int(col(9,entries[(entries_start-i-1)*num_dev+j])))/(2*bwp)
			pkt=int(col(4,entries[(entries_start-i)*num_dev+j]))				
			if pkt!=0:
				Psize = float(col(3,entries[(entries_start-i)*num_dev+j]))/pkt
			else:
				Psize = 1000
			delay = float(col(9,entries[(entries_start-i)*num_dev+j]))*Psize/float(max_bw[j])
				#print int(col(9,entries[(entries_start-i)*num_dev+j]))
				
			#else:
				#delay = 0.0
			delay_sum+=delay
		l.append(idx-i)
		l.append(delta_t[(entries_start-i)*num_dev])
		l.append(min(b))#give me available bandwidth
		l.append(delay_sum)
		jpip_stats.append(l)

def resolve_idx(path,idx,earliest_idx,num_entries,delta_t,num_dev):
	'''
	The logic of requested earliest_idx and num_entries
	'''
	del jpip_stats[:]
	if num_entries >= MAX_BUF or num_entries >= idx or earliest_idx > idx or num_entries < 0 or earliest_idx < 0:
		'''
		if any outliers is requested, return nothing
		'''
		jpip_stats.append(" ") #if anything is outbound return nothing
		return	

	if num_entries==0 and earliest_idx ==0:
		'''
		if both num_entries and earliest_idx are 0, simply calculate all available entries obtained
		'''
		if idx-MAX_BUF>=0:
			'''
			when tcshow has already generated more than 100 entries[], calculate the latest 99 results for jpip_stats[],
			(as bw is calculated based on two entries[], we can only calculate MAX_BUF-1 number of entries)
			'''
			cal_bw_delay(MAX_BUF-1,MAX_BUF-1,idx,delta_t,num_dev)			
		else:
			'''
			if tcshow has not yet generated 100 entries, display all entries.
			idx keeps track of the latest entry index
			'''
			cal_bw_delay(idx,idx,idx,delta_t,num_dev)
	elif num_entries!=0 and earliest_idx ==0:
		'''
		if only num_entries are specified, calulate the latest results from entries[] with length num_entries or idx,
		based on the generated number of entries[]
		'''
		if idx-MAX_BUF>=0:
			'''
			when tcshow has already generated more than 100 entries, calculate the latest num_entries entries[],
			and start from the index MAX_BUF-1
			'''
			cal_bw_delay(num_entries,MAX_BUF-1,idx,delta_t,num_dev)
		else:
			'''
			if tcshow has not yet generated 100 entries, calculate the latest num_entries entries[],
			but start from idx 
			'''
			cal_bw_delay(num_entries,idx,idx,delta_t,num_dev)
	elif num_entries==0 and earliest_idx !=0:
		'''
		if only earliest_idx is specified, calculate jpip_stats[] from this index onwards
		'''
		if idx-MAX_BUF>=0:
			'''
			still, more than 100 entries
			'''
			if earliest_idx < idx-MAX_BUF:
				'''
				where is the location of earliest_idx?
				if it is too small (already passed for a while),
				calculate all entries[]
				See the following explanation:
							|    entries[]   |
				----|-------------------|----------------|--->t
				earliest_idx         idx-MAX_BUF        idx
				'''
				cal_bw_delay(MAX_BUF-1,MAX_BUF-1,idx,delta_t,num_dev)
			else:
				'''
				if it is within the range,calculate entries starting from earliest_idx
						      |calculated_entries|
				    |              entries[]             |
				----|-----------------|------------------|--->t
				idx-MAX_BUF        earliest_idx         idx
				'''
				cal_bw_delay(idx-earliest_idx,MAX_BUF-1,idx,delta_t,num_dev)
		else:
			cal_bw_delay(idx-earliest_idx,idx,idx,delta_t,num_dev)
	else:
		'''
		if both are specified, calculate jpip_stats[] based on the two specification
		'''
		if idx-MAX_BUF>=0:
			if idx-num_entries < earliest_idx:
				cal_bw_delay(idx-earliest_idx,MAX_BUF-1,idx,delta_t,num_dev)
			else:
				cal_bw_delay(num_entries,MAX_BUF-1,idx,delta_t,num_dev)
		else:
			if idx-num_entries < earliest_idx:
				cal_bw_delay(idx-earliest_idx,idx,idx,delta_t,num_dev)
			else:
				cal_bw_delay(num_entries,idx,idx,delta_t,num_dev)

class monitor_stats(threading.Thread):
	'''
	a thread for monitoring tc
	once get_Stat is flagged, record the time interval delta_t 
	tcshow updates num_dev entries which are the stats grabbed from tc and return num_dev

	'''
	def __init__(self,path,interval_sec = 0.05):
		super(monitor_stats, self).__init__()
		self.runTime = interval_sec
		self.path = path
		self.keeprunning = 1
	def run(self):
		try:
			num_dev = 0
			idx=0
			delta_t = 0
			prev_t = 0
			global get_Stat
			global called
			while self.keeprunning:
				if get_Stat: #if the flag is triggered,run the following code 
					t= time.time()
					delta_t = float(t) - float(prev_t)#get time difference
					prev_t = t
					if delta_t < 0:
					 	delta_t =  self.runTime
					num_dev=tcshow(idx,self.path,delta_t) # tell me the stats along the path 
					get_Stat=False
					if idx >= MAX_BUF: #ensure max 100 entries
						del entries[0:num_dev] #keep window size to be 100
					idx+=1  #keep track of index
					
				if num_dev!=0:
					if called: #if a http request is called, send the current idx and entries[] to q.
						q.put(idx-1)
						q.put(entries)
						called = False
		except KeyboardInterrupt:
				print "stoptimer"
				self.stop()

	def stop(self):			
		self.keeprunning = 0

def return_stats(path,earliest_idx,num_entries):
	'''
	this function is also called by statscollector.py
	
	'''
	global called
	called = True
	num_dev=len(path)
	idx = q.get()
	returned_entries=q.get()
	delta_t = col(10,returned_entries)
#	print returned_entries
	resolve_idx(path,idx,earliest_idx,num_entries,delta_t,num_dev)
	return jpip_stats

class Timer2(threading.Thread):
	"""
	Timing whether it should go to sleep
	create and start the main monitor thread if everything is good
	create and start the timer which runs at the sampling rate
	"""
	def __init__(self,seconds,path,interval):
		super(Timer2, self).__init__()
		self.initime=seconds
		self.runTime=interval
		self.path = path
		self.keeprunning = seconds
		self.monthread = monitor_stats(self.path,self.runTime)	
		self.timer = Timer(self.runTime)
	def run(self):
		try:
			global monitor_run
			#global keeprun
			if not monitor_run:
				self.monthread.daemon = True
				self.monthread.start()
				self.timer.start()
				monitor_run = True
			while self.keeprunning!=0:
				print self.keeprunning
				self.keeprunning-=1
				time.sleep(1)
			print "Going to sleep now"
			self.monthread.stop()
			self.timer.stop()
			del entries[:]
			monitor_run = False
		except KeyboardInterrupt:
				print "stoptimer"
				self.stop()
	def stop(self):			
		print "KeyboardInterrupt"

	def reset(self):
		self.keeprunning = self.initime

def start_monitor(path):
	'''
	this function is called by statscollector.py
	it starts a Timer2 thread to count down so that the program goes to sleep after 10sec
	'''
	if not monitor_run: 
		if len(threads)!=0:	
			del threads[:]
		countdown = Timer2(10,path,0.05)
		countdown.start()
		threads.append(countdown)
	else:
		print "length%d"%len(threads)
		threads[0].reset()
		print "reset the time"
	return 0
     
def end_monitor(monthread):

	return 0

if __name__ == '__main__':
	monthread = monitor_stats(["eth0","eth1"],0.05)
	monthread.daemon = True
	monthread.start()
	print return_stats(["eth0","eth1"],0,0)
