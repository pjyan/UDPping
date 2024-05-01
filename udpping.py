#!/usr/bin/env python

from __future__ import print_function

import socket
import time
import string
import random
import signal
import sys
import argparse

count=0
count_of_received=0
rtt_sum=0.0
rtt_min=99999999.0
rtt_max=0.0

def signal_handler(signal, frame):
	if count!=0 and count_of_received!=0:
		print('')
		print('--- ping statistics ---')
	if count!=0:
		print('%d packets transmitted, %d received, %.2f%% packet loss'%(count,count_of_received, (count-count_of_received)*100.0/count))
	if count_of_received!=0:
		print('rtt min/avg/max = %.2f/%.2f/%.2f ms'%(rtt_min,rtt_sum/count_of_received,rtt_max))
	sys.exit(0)

def print_result():
	if count!=0 and count_of_received!=0:
		print('')
		print('--- ping statistics ---')
	if count!=0:
		print('%d packets transmitted, %d received, %.2f%% packet loss'%(count,count_of_received, (count-count_of_received)*100.0/count))
	if count_of_received!=0:
		print('rtt min/avg/max = %.2f/%.2f/%.2f ms'%(rtt_min,rtt_sum/count_of_received,rtt_max))
	sys.exit(0)

def random_string(length):
	return ''.join(random.choice(string.ascii_letters+ string.digits ) for _ in range(length))

epilog_txt = '''
examples:
  ./udpping.py 44.55.66.77 4000  -l 400 -i 2000
  ./udpping.py fe80::5400:ff:aabb:ccdd 4000
  ./udpping.py 44.55.66.77 4000 -l 400 -i 2000 -c 100')
'''
args = argparse.ArgumentParser(description='ping with UDP protocol', epilog= epilog_txt, formatter_class=argparse.RawTextHelpFormatter)
args.add_argument("dest_ip", type=str, help="destination IP address(IPv4/IPv6)")
args.add_argument("dest_port", type=int, help="destination port")
args.add_argument("-l", "--len", type=int, dest="len", help="payload length, unit:byte, default is 64", default=64)
args.add_argument("-i", "--interval", type=int, dest="interval", help="interval between each packet, unit: ms, default is 1000", default=1000)
args.add_argument("-c", "--count", type=int, dest="count", help="number of packets, default is unlimited", default=0)

args = args.parse_args()

IP=args.dest_ip
PORT=args.dest_port

is_ipv6=0

if IP.find(":")!=-1:
	is_ipv6=1

LEN =  args.len if args.len else 64
if LEN<5:
	print("LEN must be >=5")
	exit()

INTERVAL = args.interval if args.interval else 1000
if INTERVAL<50:
	print("INTERVAL must be >=50")
	exit()

if args.count:
	COUNT = args.count
	HAS_COUNT = True
else:
	COUNT = 0
	HAS_COUNT = False

signal.signal(signal.SIGINT, signal_handler)

if not is_ipv6:
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
else:
	sock = socket.socket(socket.AF_INET6,socket.SOCK_DGRAM)

print("UDPping %s via port %d with %d bytes of payload"% (IP,PORT,LEN))
sys.stdout.flush()

while True:

	if (HAS_COUNT and COUNT == count):
		print_result()

	payload= random_string(LEN)
	sock.sendto(payload.encode(), (IP, PORT))
	time_of_send=time.time()
	deadline = time.time() + INTERVAL/1000.0
	received=0
	rtt=0.0

	while True:
		timeout=deadline - time.time()
		if timeout <0:
			break
		#print "timeout=",timeout
		sock.settimeout(timeout)
		try:
			recv_data,addr = sock.recvfrom(65536)
			if recv_data== payload.encode()  and  \
					(addr[0]==IP or (is_ipv6 and (socket.inet_pton(socket.AF_INET6, addr[0]) == socket.inet_pton(socket.AF_INET6, IP)))) and \
					addr[1]==PORT:
				rtt=((time.time()-time_of_send)*1000)
				print("Reply from",IP,"seq=%d"%count, "time=%.2f"%(rtt),"ms")
				sys.stdout.flush()
				received=1
				break
		except socket.timeout:
			break
		except :
			pass
	count+=	1
	if received==1:
		count_of_received+=1
		rtt_sum+=rtt
		rtt_max=max(rtt_max,rtt)
		rtt_min=min(rtt_min,rtt)
	else:
		print("Request timed out")
		sys.stdout.flush()

	time_remaining=deadline-time.time()
	if(time_remaining>0):
		time.sleep(time_remaining)

