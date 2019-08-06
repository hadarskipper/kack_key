#Coded by baruch levin for TAS 17/12/2018
#Changed for raw data record by Andrei Nekrasov 30/1/2019

import socket
import time
from datetime import datetime
import struct
import os
import sys

def packets_generator(dir_name, segment_size=1400):
    packets = bytes(0)
    for f in os.listdir(dir_name):
        with open(os.path.join(dir_name, f), 'rb') as rec:
            packets = packets + rec.read()
    i = 0
    while True:
        yield packets[i:i+segment_size]
        i += segment_size
        i = i % len(packets)

def main():
    max_minutes = int(sys.argv[1])
    UDP_IP = "127.0.0.1"
    UDP_PORT = 5404
    sock_t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    packets_gen = packets_generator('data')
    message_T = 0.001024
    segments_per_message = 10
    segment_T = message_T / segments_per_message
    start_time = time.time()
    end_time = start_time + max_minutes*60
    curr_send_time = start_time
    print_time = 1
    while curr_send_time < end_time:
        if curr_send_time - start_time > print_time:
            print('time from start: real={} - alleged={}'.format(time.time() - start_time, curr_send_time - start_time))
            print_time += 1
        sock_t.sendto(next(packets_gen), (UDP_IP, UDP_PORT))
        curr_send_time += segment_T
        try:
            time.sleep(curr_send_time - time.time())
        except:
            pass

if __name__ == '__main__':
    main()