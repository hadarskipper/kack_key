import numpy as np
import time


class Model1Runner:
    def __init__(self):
        self.name = 'algo_par1'
        self.t_predict = 30
        self.t_overlap = 10
        self.n_laps_predict = 5

    def run(self, out_dic, live_chanel, live_idx):
        proba_list = [np.zeros((3,)) for _ in range(self.n_laps_predict)]
        curr_time = time.time()
        while True:
            data = get_last_T_data(live_chanel, live_idx, self.t_predict)
            proba = predict_proba(data)
            proba_list.pop(0)
            proba_list.append(proba)
            pred, conf = agg_time(proba_list)
            out_dic[self.name] = pred
            out_dic[self.name+'_conf'] = conf
            curr_time += self.t_overlap
            try:
                time.sleep(curr_time - time.time())
            except:
                pass


def predict_proba(x_arr):
    time.sleep(1)
    return np.random.random((3,))


def agg_time(proba_list):
    proba_mean = np.mean(np.stack(proba_list, axis=0), axis=0)
    return np.argmax(proba_mean), np.max(proba_mean)


def get_last_T_data(live_chanel, live_idx, T):
    return None
