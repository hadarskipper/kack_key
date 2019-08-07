import multiprocessing as mp
import numpy as np

def worker(shared_arr, i, v):
    shared_arr[i*5:(i+1)*5] = [v for _ in range(5)]


if __name__ == '__main__':
    X = mp.RawArray('f', 50)

    print(np.frombuffer(X, dtype='float32'))

    process_list = []
    for i in range(10):
        p = mp.Process(target=worker, args=(X, i, i**2))
        process_list.append(p)

    for p in process_list:
        p.start()

    for p in process_list:
        p.join()

    print(np.frombuffer(X, dtype='float32'))