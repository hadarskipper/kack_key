import socket
from threading import Thread
import multiprocessing as mp
import numpy
import time
import model_1, model_2
# import db_lib
import wave
import os


# Constants
file_min_max   = 5  # Maximum length (Minutes) for a record
T_max          = 60  # sec
CAS_fs         = 31250  # Hz
sampwidth      = 2  # bytes
N_max          = T_max * CAS_fs * sampwidth
NUM_CHANNELS   = 5
data_feed_HOST = '0.0.0.0'  # all availabe interfaces
data_feed_PORT = 5404  # arbitrary non privileged port

server_input_log = []
exit_bool        = [False]
current_prediction = {}
channel_queues     = []
channel_process    = []
model_process = [[] for _ in range(5)]

# Paths

model_list = [model_1.Model1Runner, model_2.Model2Runner]


def get_meta_message(udp_raw):
    ret = {}
    ret['seg_num'] = udp_raw[4]
    ret['mess_num'] = int.from_bytes(udp_raw[20:24], 'little')
    ret['size'] = len(udp_raw)
    return ret


# Send NumPy array, every channel at a time
# def RunModel():
#     for i in range(NUM_CHANNELS):
#         input_to_model_q.put(numpy.asarray(live_data_list[i]))

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


def writeChannel(q, arr, index):
    while True:
        if q.empty():
            pass
        elif q.get() == 'Start':
            dir_path = q.get()

            file_num = 0
            while True:
                if q.empty():
                    pass
                else:
                    q.get()
                    break

                wave_file = wave.open(os.path.join(dir_path, '{}.wav'.format(file_num)), "wb")
                wave_file.setparams((1, 2, CAS_fs, 0, 'NONE', 'not compressed'))
                curr_time = time.time()
                for i in range(file_min_max):
                    wave_file.writeframesraw(arr[index.value:] + arr[:index.value])
                    curr_time += 60
                    time.sleep(curr_time - time.time())
                wave_file.close()
                file_num += 1



def main():

    # Allocate threads
    data_feed_thread = Thread(target=data_feed, args=(False,))
    data_feed_thread.start()


    for i in range(5):
        channel_queues.append(mp.Queue())
        channel_process.append(mp.Process(target=writeChannel, args=(channel_queues[i], live_data_list[i], current_idx_list[i])))
        channel_process[i].start()

    for i in range(5):
        for model in model_list:
            model_inst = model()
            model_process[i].append(mp.Process(target=model_inst.run, args=(model_output_list[i], live_data_list[i], current_idx_list[i])))
            model_process[i][-1].start()


    curr_time = time.time()
    while True:
        if time.time()>curr_time:
            curr_time += 5
            print(model_output_list[0])

    data_feed_thread.join()


if __name__ == '__main__':
    mp.freeze_support()

    #   shared objects
    live_data_list = [mp.RawArray('b', N_max) for _ in range(5)]
    current_idx_list = [mp.RawValue('i', 0) for _ in range(5)]
    manager = mp.Manager()
    model_output_list = [manager.dict() for _ in range(5)]

    #_ Listen to the stream of data
    data_feed_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    data_feed_socket.bind((data_feed_HOST, data_feed_PORT))

    # Run
    main()
