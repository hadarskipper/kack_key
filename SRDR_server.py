import socket
from threading import Thread
from struct import Struct


def get_meta_message(udp_raw):
    ret = {}
    ret['seg_num'] = udp_raw[4]
    ret['mess_num'] = int.from_bytes(udp_raw[20:24], 'little')
    ret['size'] = len(udp_raw)
    return ret


def get_last_T_data(T):
    print('requested last {} seconds...'.format(T))
    if T > T_max:
        print('requested last {} seconds... maximum is {}'.format(T, T_max))
        return None
    else:
        N = int(T * CAS_fs) * sampwidth
        n_streams = 5
        data_dic = {}
        for i in range(n_streams):
            name = 'SRDR{}'.format(i)
            if current_idx_list[i] - N > -1:
                data_dic[name] = live_data_list[i][current_idx_list[i] - N:current_idx_list[i]]
            else:
                data_dic[name] = live_data_list[i][current_idx_list[i] - N:] + live_data_list[i][:current_idx_list[i]]
        return data_dic, CAS_fs, sampwidth


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


def data_feed(print_droped=True):
    message_id = 0
    while 1:
        if exit_bool[0]:
            print('in data_feed_thread - exit_bool is True...')
            break
        seg_raw, add = data_feed_socket.recvfrom(1400)
        meta = get_meta_message(seg_raw)
        if meta['seg_num'] == 10:
            delta_mess_id = meta['mess_num'] - message_id
            if print_droped:
                if delta_mess_id != 1:
                    print('missed {} messages! aka {} seconds...\ncontinuing from current message...'.format(delta_mess_id, 0.001024*delta_mess_id))
            message_id = meta['mess_num']
            for i in range(5):
                live_data_list[i][current_idx_list[i]:current_idx_list[i]+64] = seg_raw[872+i*64:872+(i+1)*64]
                current_idx_list[i] += 64
    print('data_feed_thread has finished...')


def client_handle(conn):
    while 1:
        if exit_bool[0]:
            print('in client_handle_thread - exit_bool is True...')
            serversocket.close()
            break
        ## TODO ##
        pass


def main():

    data_feed_thread = Thread(target=data_feed, args=(False,))
    data_feed_thread.start()

    server_input_thread = Thread(target=server_input)
    server_input_thread.start()

    client_handle_thread_list = []
    serversocket.listen(10)

    while 1:
        if exit_bool[0]:
            break
        try:
            conn, addr = serversocket.accept()
            print("[-] Connected to " + addr[0] + ":" + str(addr[1]))
            client_handle_thread_list.append(Thread(target=client_handle, args=(conn,)))
            client_handle_thread_list[-1].start()
        except:
            print('serversocket.accept() failed...')
            break


    data_feed_thread.join()
    server_input_thread.join()
    for t in client_handle_thread_list:
        t.join()

    print('finished')

if __name__ == '__main__':
    T_max = 60        # sec
    CAS_fs = 31250    # Hz
    sampwidth = 2     # bytes
    N_max = T_max*CAS_fs*sampwidth

    live_data_list = [bytearray(N_max) for _ in range(5)]
    current_idx_list = [0 for _ in range(5)]
    server_input_log = []
    exit_bool = [False]

    server_HOST = ''  # all availabe interfaces
    server_PORT = 9429  # arbitrary non privileged port
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((server_HOST, server_PORT))

    data_feed_HOST = '127.0.0.1'  # all availabe interfaces
    data_feed_PORT = 5404  # arbitrary non privileged port
    data_feed_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    data_feed_socket.bind((data_feed_HOST, data_feed_PORT))

    main()