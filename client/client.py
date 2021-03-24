from multiprocessing.connection import Client
from time import sleep
import socket
import subprocess


smi = 'nvidia-smi'
smi_options = [
    '--query-gpu=timestamp,name,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used',
    '--format=csv'
]


def main():
    address = ('equinox.et8.tuhh.de', 6060)
    hostname = socket.gethostname()

    while True:
        try:
            conn = Client(address, authkey=b'secret password')
        except ConnectionError:
            print("Could not connect to", address)
            sleep(10)
            continue
        else:
            print("Connected to", address)
            break

    try:
        while True:
            result = subprocess.run([smi]+smi_options, capture_output=True)
            result = str(result.stdout).split('\\n')
            result = [r.split(',') for r in result[1:-1]]
            [print(r) for r in result]
            mem_max = sum([float(r[5][:-4]) for r in result])
            mem_used = sum([float(r[7][:-4]) for r in result])
            conn.send([hostname, (mem_used/mem_max)*100])
            sleep(5)
    except KeyboardInterrupt:
        conn.send('close')
        conn.close()
        exit()
    except BrokenPipeError:
        print("Connection to server lost.")
        return


if __name__ == "__main__":
    while True:
        main()
