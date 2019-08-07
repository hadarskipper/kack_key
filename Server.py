import socket
from threading import Thread
import multiprocessing as mp
import numpy
import soundfile
import model_1, model_2
import sqlalchemy
import struct
import wave


# Constants
T_max          = 60  # sec
CAS_fs         = 31250  # Hz
sampwidth      = 2  # bytes
N_max          = T_max * CAS_fs * sampwidth
NUM_CHANNELS   = 5
data_feed_HOST = '0.0.0.0'  # all availabe interfaces
data_feed_PORT = 5404  # arbitrary non privileged port

live_data_list   = [mp.RawArray('b', N_max) for _ in range(5)]
current_idx_list = [mp.RawValue('i', 0) for _ in range(5)]
server_input_log = []
exit_bool        = [False]
current_prediction = {}
# Paths
PATH_RECORDING = r'C:\PS\{}\{}\{}.wav'
manager = mp.Manager()
model_output = manager.dict()

model_list = [model_1.Model1Runner, model_2.Model2Runner]


def get_meta_message(udp_raw):
    ret = {}
    ret['seg_num'] = udp_raw[4]
    ret['mess_num'] = int.from_bytes(udp_raw[20:24], 'little')
    ret['size'] = len(udp_raw)
    return ret


def server_input():
    while 1:
        if exit_bool[0]:
            print('in server_input_thread - exit_bool is True...')
            break
        s = input(' * q - exit \nenter new message for server: ')
        server_input_log.append(s)

        if server_input_log[-1] == 'q':
            exit_bool[0] = True
            serversocket.close()
        else:
            pass
    print('server_input_thread has finished...')

# Send NumPy array, every channel at a time
def InputToModel():
    for i in range(NUM_CHANNELS):
        input_to_model_q.put(numpy.asarray(live_data_list[i]))

def OutputFromModel():
    for i in range(NUM_CHANNELS):
        output_from_model_q.get()

def data_feed(print_droped=True):
    while 1:
        if exit_bool[0]:
            print('in data_feed_thread - exit_bool is True...')
            break
        seg_raw, add = data_feed_socket.recvfrom(1400)
        meta = get_meta_message(seg_raw)
        if meta['seg_num'] == 10:
            for i in range(5):
                live_data_list[i][current_idx_list[i].value:current_idx_list[i].value+64] = seg_raw[872+i*64:872+(i+1)*64]
                current_idx_list[i].value += 64
                current_idx_list[i].value %= 64
    print('data_feed_thread has finished...')

def writeChannels():
    soundfile.write(PATH_RECORDING, data, CAS_fs)
def client_handle(conn):
    while 1:
        if exit_bool[0]:
            print('in client_handle_thread - exit_bool is True...')
            serversocket.close()
            break
        ## TODO ##
        pass

def recordChannel(channel):



def main():

    # Allocate threads
    data_feed_thread = Thread(target=data_feed, args=(False,))
    data_feed_thread.start()

    server_input_thread = Thread(target=server_input)
    server_input_thread.start()

    data_feed_thread.join()
    server_input_thread.join()


if __name__ == '__main__':

    #_ Listen to the stream of data
    data_feed_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    data_feed_socket.bind((data_feed_HOST, data_feed_PORT))

    # Run
    main()
