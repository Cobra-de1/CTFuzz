import gym
from gym import spaces
import datetime
import os
import numpy as np
import xxhash

import ctfuzz.coverage as coverage
from ctfuzz.coverage import PATH_MAP_SIZE
# from ctfuzz.envs.fuzz_mutator import *
from ctfuzz.envs.fuzz_mutator_3 import *

import os
import timeit

PATH_MAP_SIZE_STATES = PATH_MAP_SIZE // 0x100
DEFAULT_INPUT_MAXSIZE = 0x10000
DEFAULT_MAX_MUTATION_PER_LOOP = 1000000
DEFAULT_POC_PATH = '/tmp/ctfuzz-tmp/'
DEFAULT_MIN_ENERGY = 50
DEFAULT_STOP_SOON = 5000
ACTION_MAX_TRY = [10, 10, 10, 10, 10, 10, 10, 10, 10]
# ACTION_MAX_TRY = [2, 2, 2, 2, 2, 10, 10, 10, 2]
SAVED_TRY = 200000

class CTFuzz2Env(gym.Env):
    def __init__(self):
        self.target_path = ''
        self.args = []
        self.input_maxsize = DEFAULT_INPUT_MAXSIZE

        self._seed = []

        self.poc_path = DEFAULT_POC_PATH     

        self.engine = None
        self.mutator = FuzzMutator3(self.input_maxsize)
        self.mutate_size = self.mutator.Get_action_table_size()

        self.observation_space = spaces.Box(0, 255, shape=(self.input_maxsize,), dtype='uint8')  
        
        self.action_space = spaces.Discrete(self.mutate_size)  

        # Coverage_map
        self.virgin_map = [0] * PATH_MAP_SIZE
        
        # Unique path
        self.unique_path = set()

        # Hash calculator
        self.cov_hash = xxhash.xxh64()  

        # Seed queue (info_seed struct: [seed, [action checklist], exec_time, coverage, hash])
        self.seed_queue = [] 
        self.seed_queue_2 = [] 

        # Save history
        self.history = []

        # Debug option
        self.debug = 0   

        # Seed selection and seed schedule
        self.current_seed = []   
        self.index = 0   
        self.local_step = 0
        self.total_mutation_per_loop = DEFAULT_MAX_MUTATION_PER_LOOP
        self.depth = 1
        self.last_find = 0
        self.min_energy = DEFAULT_MIN_ENERGY
        self.stop_soon = DEFAULT_STOP_SOON

        # Use for multiple depth
        self.saved_input = None

        # Calculate total try
        self.total_try = 0

        # Load env
        self.need_load_env = 0
        self.env_backup = None

        self.first_time = 1
            
    def reset_engine(self):
        self.engine = coverage.Afl(self.target_path, args=self.args)

    def set_target(self, path, args = [], poc_path = DEFAULT_POC_PATH, total_mutation_per_loop = DEFAULT_MAX_MUTATION_PER_LOOP, min_energy = DEFAULT_MIN_ENERGY, stop_soon = DEFAULT_STOP_SOON):
        self.target_path = path
        self.args = args
        self.poc_path = poc_path
        self.total_mutation_per_loop = total_mutation_per_loop
        self.min_energy = min_energy
        self.stop_soon = stop_soon
        self.reset_engine()

    def set_debug(self, debug):
        # 0: No debug info
        # 1: Debug info in reset
        # 2: Detail debug info
        self.debug = debug

    def save_env(self):
        return [self.virgin_map.copy(),
                self.unique_path.copy(),
                self.seed_queue.copy(), 
                self.seed_queue_2.copy(),
                self.history.copy(),
                self.current_seed.copy(),   
                self.index,  
                self.local_step,
                self.depth,
                self.last_find,
                self.saved_input.copy() if self.saved_input else None,
                self.total_try]

    def load_env(self, env_backup, flag):
        # Load state to switch from train phase to test phase
        # 0 not load
        # 1 load env
        # 2 copy env
        if env_backup:
            assert(len(env_backup) >= 12)
            self.need_load_env = flag
            self.env_backup = env_backup.copy()

    def set_load_env(self, flag):
        self.need_load_env = flag

    def load_env_in_reset(self):
        # Load state to switch from train phase to test phase in reset function
        if self.need_load_env and self.env_backup and len(self.env_backup) >= 12:
            if self.need_load_env == 1:
                self.virgin_map = self.env_backup[0]
                self.unique_path = self.env_backup[1]
                self.seed_queue = self.env_backup[2] 
                self.seed_queue_2 = self.env_backup[3]
                self.history = self.env_backup[4]
                self.current_seed = self.env_backup[5]   
                self.index = self.env_backup[6]   
                self.local_step = self.env_backup[7]
                self.depth = self.env_backup[8]
                self.last_find = self.env_backup[9]
                self.saved_input = self.env_backup[10]
                self.total_try = self.env_backup[11]
            else:
                self.virgin_map = self.env_backup[0].copy()
                self.unique_path = self.env_backup[1].copy()
                self.seed_queue = self.env_backup[2].copy()
                self.seed_queue_2 = self.env_backup[3].copy() 
                self.history = self.env_backup[4].copy()
                self.current_seed = self.env_backup[5].copy()   
                self.index = self.env_backup[6] 
                self.local_step = self.env_backup[7]
                self.depth = self.env_backup[8]
                self.last_find = self.env_backup[9]
                self.saved_input = self.env_backup[10].copy() if self.env_backup[10] else None,
                self.total_try = self.env_backup[11]

    def print_seed_info(self, state):
        pass

    def create_state(self, seed = b''):
        return list(seed.ljust(self.input_maxsize, b'\x00'))
    
    def create_info(self, seed = None, action = None, exec_time = 0, coverage = 0, hash = None):
        if not action:
            action = [0] * self.mutate_size
        return [seed, action, exec_time, coverage, hash]
    
    def debug_information(self):
        pass

    def add_seed(self, seed):
        assert isinstance(seed, list)
        
        for i in seed:
            if isinstance(i, bytes):
                tmp = i
                if len(tmp) > self.input_maxsize:
                    print()
                    print('Seed size larger than max input size, trim seed to ' + str(self.input_maxsize))
                    tmp = tmp[:self.input_maxsize]
                self._seed.append(tmp)

    def clear_seed(self):
        self._seed = []   

    def load_seed_to_queue(self):
        # Run the first time with initial seed
        for i in range(len(self._seed)):
            data = self._seed[i]
            coverageInfo = self.engine.run(data)

            coverage = coverageInfo.total()
            coverage_path = coverageInfo.coverage_data
            exec_time = coverageInfo.exec_time
            
            self.cov_hash.reset()
            self.cov_hash.update(bytes(coverage_path))
            tmpHash = self.cov_hash.digest()            

            if self.add_to_virgin_map(coverage_path):
                info_seed = self.create_info(data, None, exec_time, coverage, tmpHash)
                self.push_to_queue(info_seed)
            else:
                self.add_to_unique_path(tmpHash)

    def reset(self):     
        self.virgin_map = [0] * PATH_MAP_SIZE

        self.unique_path = set()

        self.cov_hash = xxhash.xxh64()  

        self.seed_queue = [] 
        self.seed_queue_2 = [] 

        self.history = []

        self.current_seed = []   
        self.index = 0   
        self.local_step = 0
        self.depth = 1
        self.last_find = 0

        self.saved_input = None

        self.total_try = 0

        if self.need_load_env and self.env_backup:
            self.load_env_in_reset()
            return self.create_state(self.current_seed[self.index][0][0])            

        if len(self._seed) > 0 and self.engine:
            self.load_seed_to_queue()
            self.create_current_seed_list()
            
            return self.create_state(self.current_seed[0][0][0])
        else:
            return self.create_state()

    def add_to_virgin_map(self, coverage, virgin_map = None):
        if not virgin_map:
            virgin_map = self.virgin_map
        ans = 0
        for i in range(PATH_MAP_SIZE):
            if coverage[i] > 0 and virgin_map[i] == 0:
                virgin_map[i] = 1
                ans += 1

        return ans
    
    def add_to_unique_path(self, hash):
        self.unique_path.add(hash)
  
    def push_to_queue(self, info_seed):
        res = False
        if info_seed[4] in self.unique_path:
            # Find the info with same hash
            for i in range(len(self.seed_queue)):
                if self.seed_queue[i][4] == info_seed[4]:
                    # Compare len, time exec
                    if len(self.seed_queue[i][0]) > len(info_seed[0]):
                        # Replace seed_info with new
                        self.seed_queue[i] = info_seed
                        res = True
                    else:
                        res = False
                    break
            else:
                for i in range(len(self.seed_queue_2)):
                    if self.seed_queue_2[i][4] == info_seed[4]:
                        # Compare len, time exec
                        if len(self.seed_queue_2[i][0]) > len(info_seed[0]):
                            # Replace seed_info with new and mov it to seed_queue
                            del self.seed_queue_2[i]
                            self.seed_queue.append(info_seed)
                            res = True
                        else:
                            res = False
                        break           
        else:
            self.add_to_unique_path(info_seed[4])
            self.seed_queue.append(info_seed)
            res = True
        return res
    
    def update_seed_queue(self, info_seed, drop = False):
        res = False
        # Find the info with same hash
        for i in range(len(self.seed_queue)):
            if self.seed_queue[i][4] == info_seed[4]:     
                if drop:
                    del self.seed_queue[i]
                    self.seed_queue_2.append(info_seed)
                else:           
                    self.seed_queue[i] = info_seed
                res = True
                break
        else:
            for i in range(len(self.seed_queue_2)):
                if self.seed_queue_2[i][4] == info_seed[4]:
                    # Compare len, time exec
                    self.seed_queue_2[i] = info_seed
                    res = True
                    break  

        return res
        
    
    def schedule(self, total):
        s = max(self.total_mutation_per_loop // sum(range(total + 1)), self.min_energy)
        res = [s * i for i in range(total, 0, -1)]
        return res

    def create_current_seed_list(self):
        tmp = []
        if len(self.seed_queue) > 0:
            tmp = self.seed_queue.copy()
            tmp.sort(key=lambda row: (-row[3]))
        elif len(self.seed_queue_2) > 0:
            self.depth = 2
            tmp = self.seed_queue_2.copy()
            tmp.sort(key=lambda row: (-row[3]))
        else:
            print('Error, seed queue empty')
            exit(0)

        total = len(tmp)
        schedule = self.schedule(total)
        self.current_seed = [[tmp[i], schedule[i]] for i in range(total)]

    def check_valid_action(self, action_list, action):
        if action_list[action] >= ACTION_MAX_TRY[action]:
            return False
        return True
    
    def get_valid_action(self, action_list):
        res = []
        for i in range(len(action_list)):
            if action_list[i] < ACTION_MAX_TRY[i]:
                res.append(i)
        return res 

    def seed_selection(self):
        self.index += 1 

        if self.index >= len(self.current_seed):
            self.create_current_seed_list()
            self.index = 0

    def step_raw(self, action):
        assert self.action_space.contains(action)

        if self.local_step + 1 == self.depth:
            if self.local_step == 0:
                info_seed = self.current_seed[self.index][0]
                energy = self.current_seed[self.index][1] 
            else:
                info_seed = self.saved_input[0]
                energy = self.saved_input[1] 

            fall_action = False
            # Check if action picked have chose reach max time
            if not self.check_valid_action(info_seed[1], action):
                valid_action = self.get_valid_action(info_seed[1])
                assert(len(valid_action) > 0)
                action = valid_action[Rand(len(valid_action))]                
                fall_action = True
            # Setup mutator
            max_try, percent = self.mutator.run_action(action, info_seed[0], energy)
            total_reward = 0
            crash_info = []
            local_last_find = self.total_try
            count_interesting = 0
            while max_try:
                max_try -= 1
                self.total_try += 1

                input_data = self.mutator.next()

                coverageInfo = self.engine.run(input_data)

                coverage = coverageInfo.total()
                coverage_path = coverageInfo.coverage_data
                exec_time = coverageInfo.exec_time
                
                self.cov_hash.reset()
                self.cov_hash.update(bytes(coverage_path))
                tmpHash = self.cov_hash.digest()            

                reward = self.add_to_virgin_map(coverage_path)
                if coverageInfo.crashes > 0:
                    reward += 100
                    crash_info.append(input_data)

                if reward:
                    tmp_info = self.create_info(input_data, None, exec_time, coverage, tmpHash)                      
                    self.push_to_queue(tmp_info)
                    self.last_find = self.total_try
                    local_last_find = self.total_try                    
                else:
                    self.add_to_unique_path(tmpHash)

                # reward = (reward * 5 + max((coverage - info_seed[3]), 0)) / 100
                total_reward += reward
                count_interesting += 1

                self.history.append({'action': action, 'testcase': len(input_data), 'coverage': sum(self.virgin_map), 'reward': reward })

                if self.total_try - local_last_find > self.stop_soon:
                    break

            # Update action list in seed queue, drop to queue 2 if all action is done            
            tmp_info = info_seed.copy()
            # tmp_info[1][action] += percent
            tmp_info[1][action] += 1
            if len(self.get_valid_action(tmp_info[1])):                
                self.update_seed_queue(tmp_info)
            else:
                self.update_seed_queue(tmp_info, True)

            self.local_step = 0
            self.index += 1 

            if self.index >= len(self.current_seed):
                self.create_current_seed_list()
                self.index = 0

            if fall_action:
                total_reward = 0

            return {
                "reward": total_reward / max(count_interesting, 1),
                "state": self.create_state(self.current_seed[self.index][0][0]),
                "crash_info": crash_info,
            }
        
        else:
            if self.local_step == 0:
                info_seed = self.current_seed[self.index][0]
                energy = self.current_seed[self.index][1] 
            else:
                info_seed = self.saved_input[0]
                energy = self.saved_input[1]     
            
            # Setup mutator
            max_try, percent = self.mutator.run_action(action, info_seed[0], 1)

            crash_info = []

            self.total_try += 1

            input_data = self.mutator.next()

            coverageInfo = self.engine.run(input_data)

            coverage = coverageInfo.total()
            coverage_path = coverageInfo.coverage_data
            exec_time = coverageInfo.exec_time
            
            self.cov_hash.reset()
            self.cov_hash.update(bytes(coverage_path))
            tmpHash = self.cov_hash.digest()            

            reward = self.add_to_virgin_map(coverage_path)
            if coverageInfo.crashes > 0:
                reward += 100
                crash_info.append(input_data)

            tmp_info = self.create_info(input_data, None, exec_time, coverage, tmpHash)  

            if reward:                                    
                self.push_to_queue(tmp_info)
                self.last_find = self.total_try
            else:
                self.add_to_unique_path(tmpHash)

            # reward = (reward * 5 + max((coverage - info_seed[3]), 0)) / 100

            self.history.append({'action': action, 'testcase': len(input_data), 'coverage': sum(self.virgin_map), 'reward': reward })

            self.local_step += 1
            self.saved_input = [tmp_info.copy(), energy]

            return {
                "reward": reward,
                "state": self.create_state(self.current_seed[self.index][0][0]),
                "crash_info": crash_info,
            }

    def step(self, action):
        info = self.step_raw(action)
        reward = info['reward']

        if len(info['crash_info']):
            # done = True # stop fuzzing when have 1 crash
            done = False # keep fuzzing
            for i in range(len(info['crash_info'])):
                name = '{}-{}-{}'.format(os.path.basename(self.target_path), datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f'), i)
                print(' [+] Find {}'.format(name))
                with open(os.path.join(self.poc_path, name), 'wb') as fp:
                    fp.write(info['crash_info'][i])
        else:
            done = False

        if self.total_try >= SAVED_TRY and self.first_time:
            print('Total try: {}'.format(self.total_try))
            print('Max_coverage: {}'.format(sum(self.virgin_map)))
            print('Number of unique path: {}'.format(len(self.unique_path))) 
            print('Depth: {}'.format(self.depth))
            print('Stop time: {}'.format(timeit.default_timer())) 
            print('Last find: {}'.format(self.last_find))
            self.first_time = 0

        state = info['state']

        return state, reward, done, {}
    
