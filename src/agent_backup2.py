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
q=Queue(maxsize=3)
back_q= Queue(maxsize=1)
jpip_stats=[]
MAX_BUF=100
get_Stat=True
monitor_run = False
called = False
threads=[]

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
				#self.stop()
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
			# print j
			# print i
			# print num_dev
			# print entries_start
			# print entries_range
			# print len(entries)
			# print entries[(entries_start-i)*num_dev+j]
			# print entries[(entries_start-i-1)*num_dev+j]
			delta_sentB = int(col(3,entries[(entries_start-i)*num_dev+j]))-int(col(3,entries[(entries_start-i-1)*num_dev+j]))
			bw = float(delta_sentB)/float(delta_t[(entries_start-i)])
			b.append("%.3f"%bw)
			if bw != 0: #data in transmission, let me know the average delay in a time interval 
				delay = (int(col(8,entries[(entries_start-i)*num_dev+j]))+int(col(8,entries[(entries_start-i-1)*num_dev+j])))/(2*bw)
			else:
				delay = 0
			delay_sum+=delay

		l.append(idx-i)
		l.append("%.3f"%delta_t[(entries_start-i)])
		if max(b)>0:
			l.append(max(b))
		else:
			l.append(0.000)
		l.append("%.3f"%delay_sum)
		jpip_stats.append(l)

def resolve_idx(path,idx,earliest_idx,num_entries,delta_t,num_dev):
	del jpip_stats[:]
	if num_entries >= MAX_BUF or num_entries >= idx or earliest_idx > idx or num_entries < 0 or earliest_idx < 0:
		jpip_stats.append(" ") #if anything is outbound return nothing
		return	

	if num_entries==0 and earliest_idx ==0:
		if idx-MAX_BUF>=0:#when the moving window has 100 entries
			cal_bw_delay(MAX_BUF,MAX_BUF-1,idx,delta_t,num_dev)
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
			cal_bw_delay(num_entries,MAX_BUF-1,idx,delta_t,num_dev)
		else:
			cal_bw_delay(num_entries,idx,idx,delta_t,num_dev)
	elif num_entries==0 and earliest_idx !=0:
		if idx-MAX_BUF>=0:
			if earliest_idx < idx-MAX_BUF:
				cal_bw_delay(MAX_BUF,MAX_BUF-1,idx,delta_t,num_dev)
			else:
				cal_bw_delay(idx-earliest_idx,MAX_BUF-1,idx,delta_t,num_dev)
		else:
			cal_bw_delay(idx-earliest_idx,idx,idx,delta_t,num_dev)
	else:
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
	def __init__(self,path,interval_sec = 0.05):
		super(monitor_stats, self).__init__()
		self.runTime = interval_sec
		self.path = path
		# self.earliest_idx=earliest_idx
		# self.num_entries = num_entries
		self.keeprunning = 1
		#threading.Thread.__init__(self)
	def run(self):
		try:

			num_dev = 0
			idx=0
			delta_t = 0
			prev_t = 0
			global get_Stat
			global called
			#timer = Timer(self.runTime)
			#timer.start()
			while self.keeprunning:
				if get_Stat:
					t= time.time()
					#print t
					#print prev_t
					#print delta_t
					delta_t = float(t) - float(prev_t)
					if delta_t < 0 or delta_t >10:
					 	delta_t =  self.runTime
					num_dev=tcshow(idx,self.path,delta_t) # tell me the stats along the path 
					#if num_dev!=0:
						# if idx > 0: # give me time interval
						# 	delta_t = float(t) - float(prev_t)
							#if called:
								#q.put(delta_t)
								#resolve_idx(self.path,idx,self.earliest_idx,self.num_entries,delta_t,num_dev)
								#q.put(entries)
								#q.put(idx)
								#called = False
							#print entries
							#print jpip_stats
						#print "index: %d "%j + "Bandwidth: %f in Bps"%bw + " and queuing delay in %d s" %delay_sum
					if idx >= MAX_BUF: #ensure max 100 entries
						del entries[0:num_dev] #keep window size to be 100
					print idx
					idx+=1
					prev_t = t
					get_Stat=False

				if called:
					q.put(entries)
					q.put(idx)
					called = False


		except KeyboardInterrupt:
				print "stoptimer"
				self.stop()

	def stop(self):			
		self.keeprunning = 0
		#print "stoping the timer"

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
# 						q.put(jpip_stats)
# 						#print jpip_stats
# 					#print "index: %d "%j + "Bandwidth: %f in Bps"%bw + " and queuing delay in %d s" %delay_sum
# 				if idx >= MAX_BUF: #ensure max 100 entries
# 					del entries[0:num_dev] #keep window size to be 100
# 				idx+=1
# 				prev_t = t

# 			time.sleep(0.01) #sampling speed set for interval

			


	# except KeyboardInterrupt:
	# 	print "stop"
	# 	timer.stop()
	# 	# for items in entries:
	# 	# 	print items
	# 	# for item in jpip_stats:
	# 	# 	print item
		
	# return

def return_stats(path,earliest_idx,num_entries):
	global called
	called = True
	#back_q.put(called)
	#delta_t=q.get()
	#idx = q.get()
	
	num_dev=len(path)
	returned_entries=q.get()
	idx = q.get()
	delta_t = col(10,returned_entries)
	#idx=entries[]
	# print delta_t
	# print idx
	# print num_dev
	for item in returned_entries:
		print item
	print "lens of entries:%d"%len(returned_entries)
	print "current index: %d"%idx
	if idx > 1:
		resolve_idx(path,idx-1,earliest_idx,num_entries,delta_t,num_dev)

	return jpip_stats

	#return item
	#q.task_done()

# def start_monitor(path):
# 	countdown = Timer2(10)
# 	global monitor_run
# 	monthread = monitor_stats(path,0.05)	
# 	if not monitor_run:
# 		monthread.daemon = True
# 		monthread.start()
# 		monitor_run = True
# 		countdown.start()
# 	# else:
# 		countdown.reset()
# 	# 	print "Going to sleep now"
# 	# 	monthread.stop()
# 		#p.join()
# 		#monitor_stats(path,earliest_idx,num_entries,0.05)
# 	#first URL return nothing, but start monitoring
# 	return 0
#keeprun = Queue(maxsize=1)
class Timer2(threading.Thread):
	"""
	Timing the sampling rate
	"""
	def __init__(self,seconds,path,interval):
		super(Timer2, self).__init__()
		self.initime=seconds
		#self.runTime=seconds
		self.runTime=interval
		self.path = path
		self.keeprunning = seconds
		self.monthread = monitor_stats(self.path,self.runTime)	
		self.timer = Timer(self.runTime)
		#threading.Thread.__init__(self)
	def run(self):
		try:
			global monitor_run
			global keeprun
			#monthread = monitor_stats(self.path,self.runTime2)	
			if not monitor_run:
				self.monthread.daemon = True
				self.monthread.start()
				self.timer.start()
				monitor_run = True
			while self.keeprunning!=0:
#				print self.keeprunning
				self.keeprunning-=1
				#keeprun.put(self.runTime)
				time.sleep(1)
			print "Going to sleep now"
			print entries
			self.monthread.stop()
			self.timer.stop()
			del entries[:]
			print "deleted entries"
			print entries
			monitor_run = False

		except KeyboardInterrupt:
				print "stoptimer"
				#self.stop()
	def stop(self):			
		#self.timer.stop()
		pass

	def reset(self):
		self.keeprunning = self.initime


def start_monitor(path):
	#global monitor_run
	#monthread = monitor_stats(path,0.05)	
	if not monitor_run: 
		if len(threads)!=0:	
			del threads[:]
		countdown = Timer2(10,path,1)
		countdown.start()
		threads.append(countdown)

	else:
		print "length%d"%len(threads)
		threads[0].reset()
		print "reset the time"
	# 	print "Going to sleep now"
	# 	monthread.stop()
		#p.join()
		#monitor_stats(path,earliest_idx,num_entries,0.05)
	#first URL return nothing, but start monitoring
	return 0
     
def end_monitor(monthread):
	#monthread.stop()
	#no request after awhile 60s? stop the monitor process
	return 0

if __name__ == '__main__':
	monthread = monitor_stats(["eth0","eth1"],0.05)
	monthread.daemon = True
	monthread.start()
	#timer = Timer(0.05)
	#timer.start()
	#monthread.join()
	print return_stats(["eth0","eth1"],0,0)
