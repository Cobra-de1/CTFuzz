import gym
from gym import spaces
import datetime
import os
import numpy as np
import xxhash
import random

import ctfuzz.coverage as coverage
from ctfuzz.coverage import PATH_MAP_SIZE
from ctfuzz.envs.fuzz_mutator import *
from ctfuzz.envs.fuzz_mutator_2 import *

import os
import timeit

DEFAULT_INPUT_MAXSIZE = 0x8000
DEFAULT_POC_PATH = '/tmp/ctfuzz-tmp/'
SAVED_TRY = 200000

class OldRlfuzzEnv(gym.Env):
    def __init__(self):
        self.target_path = ''
        self.args = []
        self.input_maxsize = DEFAULT_INPUT_MAXSIZE

        self._seed = ''
        self.last_run = self._seed

        self.poc_path = DEFAULT_POC_PATH     

        self.engine = None
        self.mutator = FuzzMutator(self.input_maxsize)
        self.mutate_size = self.mutator.Get_action_table_size()

        self.observation_space = spaces.Box(0, 255, shape=(self.input_maxsize,), dtype='uint8')  
        
        self.action_space = spaces.Discrete(self.mutate_size)  

        self.input_dict = []

        # Coverage_map
        self.virgin_map = [0] * PATH_MAP_SIZE
        
        # Unique path
        self.unique_path = set()

        # Hash calculator
        self.cov_hash = xxhash.xxh64() 

        # Save history
        self.history = []

        # Debug option
        self.debug = 0   

        # Total try
        self.total_try = 0

        self.first_time = 1
            
    def reset_engine(self):
        self.engine = coverage.Afl(self.target_path, args=self.args)

    def set_target(self, path, args = [], poc_path = DEFAULT_POC_PATH):
        self.target_path = path
        self.args = args
        self.poc_path = poc_path
        self.reset_engine()

    def set_debug(self, debug):
        # 0: No debug info
        # 1: Debug info in reset
        # 2: Detail debug info
        self.debug = debug

    def print_seed_info(self, state):
        pass

    def create_state(self, seed = b''):
        return list(seed.ljust(self.input_maxsize, b'\x00'))
    
    def debug_information(self):
        pass

    def add_seed(self, seed):
        if isinstance(seed, list):
            print('Base env not support multiple seed')
            return
        if isinstance(seed, bytes):
            if len(seed) > self.input_maxsize:
                print()
                print('Seed size larger than max input size, trim seed to ' + str(self.input_maxsize))
                seed = seed[:self.input_maxsize]
            self._seed = seed
            self.last_run = self._seed

    def clear_seed(self):
        self._seed = b''  

    def reset(self):     
        # self.virgin_map = [0] * PATH_MAP_SIZE

        # self.unique_path = set()

        # self.cov_hash = xxhash.xxh64()  

        # self.history = []    

        # self.last_run = self._seed   

        return self.create_state(self.last_run)

    def add_to_virgin_map(self, coverage):
        ans = 0
        for i in range(PATH_MAP_SIZE):
            if coverage[i] > 0 and self.virgin_map[i] == 0:
                self.virgin_map[i] = 1
                ans += 1

        return ans
    
    def add_to_unique_path(self, hash):
        self.unique_path.add(hash)
  
    def step_raw(self, action):
        if not self.action_space.contains(action):
            action = np.argmax(action)
        input_data = self.mutator.mutate(action, self.last_run)

        # self.mutate_history.append(mutate)

        # self.input_len_history.append(len(input_data))

        coverageInfo = self.engine.run(input_data)

        coverage = coverageInfo.total()
        coverage_path = coverageInfo.coverage_data
        exec_time = coverageInfo.exec_time
        reward = coverageInfo.reward()
        
        self.cov_hash.reset()
        self.cov_hash.update(bytes(coverage_path))
        tmpHash = self.cov_hash.digest()            

        if self.add_to_virgin_map(coverage_path):            
            self.last_run = input_data
            self.input_dict.append(self.last_run)
        else:
            self.last_run = random.choice(self.input_dict)

        self.add_to_unique_path(tmpHash)      

        # Save to history
        # self.history.append({'seed': self.last_input_data, 'action': action, 'testcase': input_data, 'coverage': last_count_block, 'new_block': last_new_block})
        # self.history.append({'seed': self.last_input_data, 'action': action, 'testcase': input_data, 'coverage': last_count_block, 'reward': reward })
        self.history.append({'action': action, 'testcase': len(input_data), 'coverage': sum(self.virgin_map), 'reward': reward })

        self.total_try += 1

        return {
            "reward": reward,
            "state": self.create_state(self.last_run),
            "crash_info": True if coverageInfo.crashes > 0 else False,
            "input_data": input_data
        }

    def step(self, action):
        info = self.step_raw(action)
        reward = info['reward']

        if info['crash_info']:
            # done = True # stop fuzzing when have 1 crash
            done = False # keep fuzzing
            name = '{}-{}'.format(os.path.basename(self.target_path), datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f'))
            print(' [+] Find {}'.format(name))
            with open(os.path.join(self.poc_path, name), 'wb') as fp:
                fp.write(info['input_data'])
        else:
            done = False

        if self.total_try >= SAVED_TRY and self.first_time:
            print('Total try: {}'.format(self.total_try))
            print('Max_coverage: {}'.format(sum(self.virgin_map)))
            print('Number of unique path: {}'.format(len(self.unique_path))) 
            print('Stop time: {}'.format(timeit.default_timer())) 
            self.first_time = 0

        state = info['state']

        return state, reward, done, {}
    
