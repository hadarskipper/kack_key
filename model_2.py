import numpy as np
import time


class Model2Runner:
    def __init__(self, out_dic, output_key):
        self.name = 'model_2'
        self.t_predict = 30
        self.t_overlap = 10
        self.n_laps_predict = 5
        self.out_dic = out_dic
        self.output_key = output_key

    def run(self, live_chanel, live_idx):
        proba_list = [np.zeros((3,)) for _ in range(self.n_laps_predict)]
        curr_time = time.time()
        while True:
            data = get_last_T_data(live_chanel, live_idx, self.t_predict)
            proba = predict_proba(data)
            proba_list.pop(0)
            proba_list.append(proba)
            self.out_dic[self.output_key] = agg_time(proba_list)
            curr_time += self.t_overlap
            try:
                time.sleep(curr_time - time.time())
            except:
                pass


def predict_proba(x_arr):
    time.sleep(1)
    return np.random.random((3,))


def agg_time(proba_list):
    return np.argmax(np.mean(np.stack(proba_list, axis=0), axis=0))


def get_last_T_data(T):
    return None
