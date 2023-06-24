import gym
from gym import spaces
import datetime
import os
import numpy as np
import xxhash

import ctfuzz.coverage as coverage
from ctfuzz.coverage import PATH_MAP_SIZE
from ctfuzz.envs.fuzz_mutator import *

import os

PATH_MAP_SIZE_STATES = PATH_MAP_SIZE // 0x100
DEFAULT_INPUT_MAXSIZE = 0x8000 - PATH_MAP_SIZE_STATES - 13

class CTFuzz1Env(gym.Env):
    def __init__(self):
        self._target_path = ''
        self._args = []
        self._input_maxsize = DEFAULT_INPUT_MAXSIZE

        self._seed = b''

        self.POC_PATH = '/tmp/ctfuzz-tmp/'      

        self.engine = coverage.Afl(self._target_path, args=self._args)
        self.input_maxsize = self._input_maxsize 
        self.mutator = FuzzMutator(self.input_maxsize)
        self.mutate_size = self.mutator.Get_action_table_size()
        self.density_size = 256

        self.observation_space = spaces.Box(0, 255, shape=(self.input_maxsize + PATH_MAP_SIZE_STATES + 4 + 1 + 4 + 4,), dtype='uint8')  
        
        self.action_space = spaces.Discrete(self.mutate_size)  

        # Coverage_map
        self.virgin_map = [0] * PATH_MAP_SIZE

        # Testing random seed selection
        self.input_dict = {}
        self.covHash = xxhash.xxh64()     

        # Save history
        self.history = []

        # Debug option
        self.debug = 0   

        # Aflplusplus picked seed
        self.current_seed = []   
        self.count = 0   
        self.local_step = 0

        self.reset()

    def set_target(self, path, args = [], input_max_size = DEFAULT_INPUT_MAXSIZE):
        self._target_path = path
        self._args = args
        self._input_maxsize = input_max_size

    def set_debug(self, debug):
        # 0: No debug info
        # 1: Debug info in reset
        # 2: Detail debug info
        self.debug = debug

    # convert back from 4 byte big endian
    def convert(self, num):
        # print(num)
        return num[3] + (num[2] << 8) + (num[1] << 16) + (num[0] << 24)
    
    # compress coverage_path from 0x10000 to 0x100
    def compress_coverage_path(self, coverage):
        res = [0] * 0x100
        for i in range(0x100):
            for j in range(0x100):
                if coverage[j * 0x100 + i]:
                    res[i] += 1
        return res

    def print_states(self, state):
        # print(state[:DEFAULT_INPUT_MAXSIZE])
        # print('Seed: ' + (''.join([chr(i) for i in state[:DEFAULT_INPUT_MAXSIZE]])).rstrip('\x00'))
        print('Coverage path: ', end='')
        print(state[DEFAULT_INPUT_MAXSIZE: DEFAULT_INPUT_MAXSIZE + 0x100])
        print('Last exec time: ' + str(self.convert(state[DEFAULT_INPUT_MAXSIZE + 0x100: DEFAULT_INPUT_MAXSIZE + 0x100 + 4])))
        print('Last action: ' + str(state[DEFAULT_INPUT_MAXSIZE + 0x100 + 4: DEFAULT_INPUT_MAXSIZE + 0x100 + 5]))
        print('Last count block: ' + str(self.convert(state[DEFAULT_INPUT_MAXSIZE + 0x100 + 5: DEFAULT_INPUT_MAXSIZE + 0x100 + 9])))
        print('Last new block: ' + str(self.convert(state[-4:])))
        print()

    def create_states(self, seed, last_coverage, last_exec_time, last_action, last_count_block, last_new_block):
        return list(seed) + list(last_coverage) +\
                  [last_exec_time >> 24, ((last_exec_time >> 16) & 0xFF), ((last_exec_time >> 8) & 0xFF), last_exec_time & 0xFF] +\
                      [last_action] +\
                        [last_count_block >> 24, ((last_count_block >> 16) & 0xFF), ((last_count_block >> 8) & 0xFF), last_count_block & 0xFF] +\
                          [last_new_block >> 24, ((last_new_block >> 16) & 0xFF), ((last_new_block >> 8) & 0xFF), last_new_block & 0xFF]         
    
    def create_initial_states(self, seed = None):
        if seed:
            return self.create_states(list(seed), [0] * PATH_MAP_SIZE_STATES, 0, -1, 0, 0)
        return self.create_states(list([0] * self.input_maxsize), [0] * PATH_MAP_SIZE_STATES, 0, -1, 0, 0)
    
    def debug_information(self):
        print()
        print('----- Debug information -----')
        print('----- History -----')
        for i in self.history:
            print(i)
        print('----- Input dict -----')
        for i in self.input_dict:
            print(i)
        print()
    
    def set_seed(self, seed):
        assert isinstance(seed, bytes)

        if len(seed) > self._input_maxsize:
            print()
            print('Seed size larger than max input size, trim seed to ' + str(self._input_maxsize))
            seed = seed[:self._input_maxsize]
        
        self._seed = seed
        self.reset()

    def reset(self):   
        
        if self.debug:
            self.debug_information()
            # self.debug = 0

        self.engine = coverage.Afl(self._target_path, args=self._args)
        self.input_maxsize = self._input_maxsize 
        self.mutator = FuzzMutator(self.input_maxsize)
        # self.input_dict = {} 
        # self.covHash = xxhash.xxh64()

        # self.observation_space = spaces.Dict({'seed' : spaces.Box(0, 255, shape=(self.input_maxsize,), dtype='uint8'),
		# 						  				'last_coverage' : spaces.Box(0, 255, shape=(PATH_MAP_SIZE,), dtype='uint8'),
        #                                         'last_exec_time': 0,
        #                                         'last_action': -1,
        #                                         'last_new_block': 0,
		# 									  })

        self.observation_space = spaces.Box(0, 255, shape=(self.input_maxsize + PATH_MAP_SIZE_STATES + 4 + 1 + 4 + 4,), dtype='uint8')

        self.last_input_data = self._seed

        # Coverage_map
        self.virgin_map = [0] * PATH_MAP_SIZE

        # Testing random seed selection
        self.input_dict = {}
        self.covHash = xxhash.xxh64() 

        # History saving
        self.history = []

        # AFLplusplus seed pick
        self.current_seed = []
        self.count = 0
        self.local_step = 0

        if self._target_path == '':
            # assert len(self.last_input_data) <= self.input_maxsize
            self.state = self.create_initial_states(self.last_input_data.ljust(self.input_maxsize, b'\x00'))
            self.push_to_queue(b'\x00' * PATH_MAP_SIZE, self.state, self.last_input_data)

            return self.state 
        

        # Run the first time with initial seed
        self.coverageInfo = self.engine.run(self.last_input_data)

        last_count_block = self.coverageInfo.total()
        
        previous_count_block = 0
        last_new_block = last_count_block - previous_count_block

        compress_coverage_path = self.compress_coverage_path(self.coverageInfo.coverage_data)
        self.state = self.create_states(list(self.last_input_data.ljust(self.input_maxsize, b'\x00')), compress_coverage_path, self.coverageInfo.exec_time, -1, last_count_block, last_new_block)
        
        if self.debug == 2:
            print('----- Initial seed info ----')
            print('Initial seed: ')
            print(self.last_input_data)
            self.print_states(self.state)

        self.push_to_queue(bytes(self.coverageInfo.coverage_data), self.state, self.last_input_data)    
        self.add_to_virgin_map(self.coverageInfo.coverage_data)    
        
        return self.state

    def add_to_virgin_map(self, coverage):
        ans = 0
        for i in range(PATH_MAP_SIZE):
            if coverage[i] > 0 and self.virgin_map[i] == 0:
                self.virgin_map[i] = 1
                ans += 1

        return ans
  
    def push_to_queue(self, coverage_path, state, seed):
        res = False
        self.covHash.reset()
        self.covHash.update(coverage_path)
        tmpHash = self.covHash.digest()
        if tmpHash in self.input_dict:
            # Compare last_new_block
            items = self.input_dict[tmpHash]
            if len(seed) < len(items[1]): # AFLplusplus chose the seed with smaller size
                if self.debug == 2:
                    print()
                    print('----- Replace state in queue -----')
                    print('Hex: ', end = '')
                    print(tmpHash)
                    print('----- Old state -----')
                    self.print_states(items[0])
                    items = [state, seed]
                    print('----- New state -----')
                    self.print_states(items[0])
                res = True
            self.input_dict[tmpHash] = items
        else:
            self.input_dict[tmpHash] = [state, seed]
            res = True
            if self.debug == 2:
                print()
                print('----- Push state to queue -----')
                self.print_states(state)
        return res
    
    def create_current_seed_list(self):
        return list(self.input_dict.values())

    def seed_selection(self, input_data, new_state):
        self.count += 1 

        if self.count >= len(self.current_seed):
            self.current_seed = self.create_current_seed_list()
            self.count = 0
            if self.debug == 2:
                print()
                print('----- Seed selection -----')
                print('Create current seed list!!!')
                # print(self.input_dict)
                # print(self.current_seed)
        
        if self.current_seed or len(self.current_seed):            
            next_item = self.current_seed[self.count]

            if self.debug == 2:
                print()
                print('----- Seed selection -----')
                print('Next input: ', end = '')
                print(next_item[1])
                print('Next state:')
                self.print_states(next_item[0])

            return next_item[1], next_item[0]
        else:
            if self.debug == 2:
                print()
                print('----- Current seed list error or empty, use old input and state -----')
                print()
            return input_data, new_state

    def step_raw(self, action):
        assert self.action_space.contains(action)
        input_data = self.mutator.mutate(action, self.last_input_data)

        # self.mutate_history.append(mutate)

        # self.input_len_history.append(len(input_data))

        self.coverageInfo = self.engine.run(input_data)

        last_count_block = self.coverageInfo.total()
        # print('last count block: ' + str(last_count_block))
        previous_count_block = self.convert(self.state[self.input_maxsize + PATH_MAP_SIZE_STATES + 4 + 1: self.input_maxsize + PATH_MAP_SIZE_STATES + 4 + 1 + 4])
        last_new_block = last_count_block - previous_count_block

        if self.debug == 2:
            print('----- Step raw debug ----')
            print('Picked seed: ')
            print(self.last_input_data)
            print('Seed coverage: ' + str(previous_count_block))
            print('Action pick: ' + str(action))
            print('Testcase generate: ', end = '')
            print(input_data)
            print('New coverage: ' + str(last_count_block))
            print()
        
        compress_coverage_path = self.compress_coverage_path(self.coverageInfo.coverage_data)
        new_state = self.create_states(list(input_data.ljust(self.input_maxsize, b'\x00')), compress_coverage_path, self.coverageInfo.exec_time, action, last_count_block, last_new_block)
        
        # print('last new block: ' + str(last_new_block))
        # print(len(new_state))
        # print(len(self.coverageInfo.coverage_data))

        new_coverage = self.add_to_virgin_map(self.coverageInfo.coverage_data)

        if new_coverage:
            new_hash = self.push_to_queue(bytes(self.coverageInfo.coverage_data), new_state, input_data)

        last_new_block = max(last_new_block, 0) # // PATH_MAP_SIZE # Try to avoid negative reward

        reward = new_coverage
        # if new_hash:
        #     reward += 5

        # Scale reward for not too high
        reward = min(reward, 100) / 100

        # Save to history
        # self.history.append({'seed': self.last_input_data, 'action': action, 'testcase': input_data, 'coverage': last_count_block, 'new_block': last_new_block})
        # self.history.append({'seed': self.last_input_data, 'action': action, 'testcase': input_data, 'coverage': last_count_block, 'reward': reward })
        self.history.append({'action': action, 'testcase': len(input_data), 'coverage': last_count_block, 'reward': reward })

        # Try 10 continue mutate per time
        if self.local_step >= 40:
            self.local_step = 0
            self.last_input_data, self.state = self.seed_selection(input_data, new_state)
        else:
            self.local_step += 1
            self.last_input_data, self.state = input_data, new_state


        return {
            "reward": reward,
            "state": self.state,
            "crash_info": True if self.coverageInfo.crashes > 0 else False,
            "input_data": input_data
        }

    def step(self, action):

        info = self.step_raw(action)
        reward = info['reward']
        # assert reward <= 1

        if info['crash_info']:
            # done = True # stop fuzzing when have 1 crash
            done = False # keep fuzzing
            name = '{}-{}'.format(os.path.basename(self._target_path), datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f'))
            print(' [+] Find {}'.format(name))
            with open(os.path.join(self.POC_PATH, name), 'wb') as fp:
                fp.write(info['input_data'])
        else:
            done = False

        state = info['state']
        # print(len(state))

        # assert len(state) == self.input_maxsize, '[!] len(state)={}, self.input_maxsize={}'.format(len(state), self.input_maxsize)
        
        # Return format to gym rl-agent
        return state, reward, done, {}

    # def render(self, mode='human', close=False):
    #     pass

    # def eof(self):
    #     return self._dict.eof()

    # def dict_size(self):
    #     return self._dict.size()

    def input_size(self):
        return self.input_maxsize

    def get_poc_path(self):
        return self.POC_PATH
