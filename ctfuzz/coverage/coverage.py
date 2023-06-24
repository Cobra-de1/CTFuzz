import subprocess
import os
import time
import mmap
import struct
import signal

from posix_ipc import SharedMemory, Semaphore, ExistentialError

PATH_MAP_SIZE = 0x10000
_process = None

SHARED_MEM_SIZE = 65541
SHARED_MEM_NAME = '/shared_mem'
SEM_INPUT_NAME = '/sem_input'
SEM_OUTPUT_NAME = '/sem_output'

def signal_handler(signal, frame):
    global _process

    if _process is not None:
        _process.terminate()

signal.signal(signal.SIGINT, signal_handler)

class Coverage:
    def __init__(self, coverage_status=None, exec_time=None, coverage_data=None):
        self.crashes = 0
        self.exec_time = exec_time

        assert coverage_status is not None
        assert coverage_data is not None
        assert exec_time is not None

        # Something corrupt when coverage data not have same size with PATH_MAP_SIZE, temp fix
        if len(coverage_data) != PATH_MAP_SIZE:
            print('\nSomething corrupt in getting coverage data')
            coverage_data = b'\x00' * PATH_MAP_SIZE

        self.exec_time = exec_time
        self.coverage_data = list(coverage_data)
        if coverage_status == 2:
            self.crashes = 1

    # Reward
    def reward(self):
        return self.total() / PATH_MAP_SIZE
        # return self.total()
    
    def debug(self):
        print('Len: ' + str(len(self.coverage_data)))
        print('Total: ' + str(self.total()))
    
    # Get total of non zero block
    def total(self):
        total = sum(self.coverage_data)
        return total

"""
AFL ENGINE
"""


class Afl:
    def __init__(self, target_path, args=[]):
        self.process = None
        if target_path == '' or target_path == None:
            return
        self.env = os.environ.copy()
        self.tmp = '/tmp/ctfuzz-tmp/'
        self.tmp_in = self.tmp + 'in/'
        self.tmp_out = self.tmp + 'out/'
        self.poc_path = self.tmp + 'poc-'
        if not os.path.isdir(self.tmp):
            os.mkdir(self.tmp)
        if not os.path.isdir(self.tmp_in):
            os.mkdir(self.tmp_in)
        if not os.path.isdir(self.tmp_out):
            os.mkdir(self.tmp_out)
        self.forkserver_path = 'ex-frsv'
        self.cmd = [
            self.forkserver_path,
            "-O",
            "-C",
            '-i', self.tmp_in,
            '-o', self.tmp_out,
            '--',
            target_path,
        ]
        self.cmd += args
        # ./ex-frsv -i /tmp/afl-temp-in -o /tmp/afl-temp-out -O -C -- ../../bins/base64 -d @@

        self.process = subprocess.Popen(
            self.cmd,
            env=self.env,
        )

        time.sleep(1)

        for i in range(20):
            try:
                self.shared_memory_info = SharedMemory(SHARED_MEM_NAME)
                break
            except ExistentialError as e:
                print('[!] ERROR: {} {}'.format(e, SHARED_MEM_NAME))
                time.sleep(1)

        self.shared_memory = mmap.mmap(self.shared_memory_info.fd, 0)

        self.sem_input = Semaphore(SEM_INPUT_NAME)
        self.sem_output = Semaphore(SEM_OUTPUT_NAME)
        
        global _process        

        _process = self.process

    def run(self, input_data):
        input_len = struct.pack(">I", len(input_data))

        self.shared_memory.seek(0)
        self.shared_memory.write(input_len + input_data)

        self.sem_input.release()

        self.sem_output.acquire()

        output_bytes = self.shared_memory[:]

        status = output_bytes[0]
        time = struct.unpack('>I', output_bytes[1:5])[0]
        coverage_data = output_bytes[5:PATH_MAP_SIZE + 5] 
        return Coverage(status, time, coverage_data)

    def __del__(self):
        global _process

        if _process == self.process:
            _process = None

        if self.process is not None:
            self.process.terminate()


# # Test
# engine = Afl('../../bins/base64', ['-d', '@@'])
# if len(sys.argv) > 1:
#     f = open(sys.argv[1], 'rb+')
#     input_bytes = f.read()
#     print(input_bytes)
#     f.close()
# else:
#     input_bytes = b"Hello, world!"
# cov = engine.run(input_bytes)
# cov.debug()
# print(cov.crashes)
# print(cov.exec_time)
# print(cov.reward())
# _process.terminate()
