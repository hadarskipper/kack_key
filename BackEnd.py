from flask import Flask, json, request
import socket
from threading import Thread
import multiprocessing as mp
import time
import wave
import os
import numpy as np
import datetime

# Local imports
import model_1
import model_2
import DAL

api = Flask(__name__)

# Constants
file_min_max   = 5  # Maximum length (Minutes) for a record
packets_n      = 1000*60  #  about 60 sec
N_max          = packets_n*64
CAS_fs         = 31250  # Hz
sampwidth      = 2  # bytes
T_max          = N_max/sampwidth/CAS_fs
NUM_CHANNELS   = 5
chanel_list = list(range(NUM_CHANNELS))
output_dic_template = dict([('algo_par{}'.format(i), -1.0) for i in range(1, 11)] +
                           [('algo_par{}_conf'.format(i), 0.0) for i in range(1, 11)])



data_feed_HOST = '127.0.0.1'  # all available interfaces
data_feed_PORT = 5404  # arbitrary non privileged port
OK_STATUS      = [{'Status': 'OK'}]
N_OK_STATUS    = [{'Status': 'Not OK'}]

channel_queues = []


model_list = [model_1.Model1Runner, model_2.Model2Runner]

################################  WEB  #################################
@api.route('/GetAllChannels', methods=['GET'])
def get_all_channels():
    return json.dumps(chanel_list)


@api.route('/GetRecordStatus', methods=['GET'])
def get_record_status():
    channel = int(request.args['Channel'])
    isChannelRecording = [{'IsRecording': is_recording[channel]}]
    return json.dumps(isChannelRecording)



@api.route('/GetSummaryPanel', methods=['GET'])
def get_summary_panel():
    for channel in chanel_list:
        repo.recordTag.getLastTagByChannelId(channel)

    return json.dumps(OK_STATUS)


@api.route('/GetModelData', methods=['GET'])
def get_model_data():
    channel = int(request.args['Channel'])
    return json.dumps(model_output_list[channel])


@api.route('/TagRecording', methods=['POST'])
def tag_recording():
    RecordID  = int(request.args['RecordID'])
    algo_par1 = int(request.args['algo_par1'])
    algo_par2 = int(request.args['algo_par2'])
    algo_par3 = int(request.args['algo_par3'])
    algo_par4 = int(request.args['algo_par4'])
    algo_par5 = int(request.args['algo_par5'])
    algo_par6 = int(request.args['algo_par6'])
    algo_par7 = int(request.args['algo_par7'])
    algo_par8 = int(request.args['algo_par8'])
    algo_par9 = int(request.args['algo_par9'])
    algo_par10 = int(request.args['algo_par10'])
    user_par1 = int(request.args['user_par1'])
    user_par2 = int(request.args['user_par2'])
    user_par3 = int(request.args['user_par3'])
    user_par4 = int(request.args['user_par4'])
    user_par5 = int(request.args['user_par5'])
    user_par6 = int(request.args['user_par6'])
    user_par7 = int(request.args['user_par7'])
    user_par8 = int(request.args['user_par8'])
    user_par9 = int(request.args['user_par9'])
    user_par10 = int(request.args['user_par10'])
    timestamp = str(datetime.datetime.now()).replace(' ', 'T')
    repo.recordTag.insert(RecordID, algo_par1, user_par1, algo_par2, user_par2, algo_par3, user_par3, algo_par4, user_par4, algo_par5, user_par5, algo_par6, user_par6, algo_par7, user_par7, algo_par8, user_par8, algo_par9, user_par9,algo_par10, user_par10, timestamp)
    return json.dumps(OK_STATUS)


@api.route('/StartRecord', methods=['POST'])
def start_record():
    channel = int(request.args['Channel'])
    timestamp = request.args['timestamp']

    # Checking if recording was stopped because it ran for too long
    if not channel_queues[channel].empty():
        if  channel_queues[channel].get() == 'Stopped':
            is_recording[channel] = False

    if is_recording[channel]:
        return json.dumps(N_OK_STATUS)

    channel_queues[channel].put('Start')
    channel_queues[channel].put(repo.records.insert(channel, timestamp))
    return json.dumps(OK_STATUS)


@api.route('/StopRecord', methods=['POST'])
def stop_record():
    channel = int(request.args['Channel'])
    timestamp = request.args['timestamp']

    if not is_recording[channel]:
        return json.dumps(N_OK_STATUS)

    channel_queues[channel].put('Stop')
    channel_queues[channel].put(timestamp)
    is_recording[channel] = False
    return json.dumps(OK_STATUS)

############################################################################

def get_meta_message(udp_raw):
    ret = {}
    ret['seg_num'] = udp_raw[4]
    ret['mess_num'] = int.from_bytes(udp_raw[20:24], 'little')
    ret['size'] = len(udp_raw)
    return ret


def data_feed():
    while 1:
        seg_raw, add = data_feed_socket.recvfrom(1400)
        meta = get_meta_message(seg_raw)
        if meta['seg_num'] == 10:
            for i in range(5):
                live_data_list[i][current_idx_list[i].value:current_idx_list[i].value+64] = seg_raw[872+i*64:872+(i+1)*64]
                current_idx_list[i].value += 64
                current_idx_list[i].value %= 64


def writeChannel(q, arr, index, channel):
    time.sleep(T_max)

    arr = np.frombuffer(arr, dtype='uint8')

    while True:

        if q.empty():
            pass

        elif q.get() == 'Start':
            dir_path = q.get()
            os.makedirs(dir_path, exist_ok=True)
            file_num = 0

            while True:

                if q.empty():
                    pass

                else:

                    if 'Stop' == q.get():
                        timestamp = str(datetime.datetime.now()).replace(' ', 'T')
                        repo = DAL._Repository()
                        repo.records.update(dir_path.split('\\')[-1], timestamp)
                        break

                    elif file_num * file_min_max > 120: # Quit after 2 hours
                        repo = DAL._Repository()
                        repo.records.update()
                        q.put('Stopped')
                        break

                wave_file = wave.open(os.path.join(dir_path, '{}.wav'.format(file_num)), "wb")
                wave_file.setparams((1, 2, CAS_fs, 0, 'NONE', 'not compressed'))
                curr_time = time.time()

                for i in range(file_min_max):
                    raw = np.concatenate([arr[index.value:], arr[:index.value]])
                    wave_file.writeframesraw(raw)
                    curr_time += T_max
                    time.sleep(curr_time - time.time())

                wave_file.close()
                file_num += 1


def main():

    # Allocate processes
    channel_process = []
    model_process   = []

    # Allocate thread for data feed
    data_feed_thread = Thread(target=data_feed, args=(False,))
    data_feed_thread.start()

    for i in range(NUM_CHANNELS):
        channel_queues.append(mp.Queue())
        channel_process.append(mp.Process(target=writeChannel, args=(channel_queues[i], live_data_list[i], current_idx_list[i], i)))
        channel_process[i].start()

    for i in range(NUM_CHANNELS):
        model_process[i] = []

        for model in model_list:
            model_inst = model()
            model_process[i].append(mp.Process(target=model_inst.run, args=(model_output_list[i], live_data_list[i], current_idx_list[i])))
            model_process[i][-1].start()

    # Run interface with web
    api.run()


if __name__ == '__main__':

    mp.freeze_support()
    repo = DAL._Repository()
    #   shared objects
    manager = mp.Manager()
    live_data_list    = [mp.RawArray('b', N_max) for _ in range(5)]
    current_idx_list  = [mp.RawValue('i', 0) for _ in range(5)]
    model_output_list = [manager.dict(output_dic_template) for _ in range(5)]
    is_recording      = [False for _ in range(NUM_CHANNELS)]

    #_Listen to the stream of data
    data_feed_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    data_feed_socket.bind((data_feed_HOST, data_feed_PORT))

    # Run
    main()