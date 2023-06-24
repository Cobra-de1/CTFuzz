import warnings
warnings.filterwarnings('ignore',category=FutureWarning)

import numpy as np
import gym
import sys
import timeit
from tqdm import tqdm

# pip install .
import ctfuzz

# pip install tensorflow
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Conv1D, Dense, Flatten, MaxPooling1D, Reshape, BatchNormalization
from tensorflow.keras.optimizers import Adam

# pip install keras-rl2
from rl.agents import DQNAgent
from rl.memory import SequentialMemory
from rl.policy import EpsGreedyQPolicy

start = timeit.default_timer()

number = 0
if len(sys.argv) > 1:
    number = int(sys.argv[1])

with open('list.txt', 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    TARGET = lines[number * 3]
    target_path = lines[number * 3 + 1].split(',')[0]
    target_args = lines[number * 3 + 1].split(',')[1:]
    seed_path = lines[number * 3 + 2]

ENV_NAME = 'BaseEnv-v0'
env = gym.make(ENV_NAME)
env.set_target(target_path, target_args)

with open(seed_path, 'rb') as f:
    seed = f.read()

env.add_seed([seed])

env.set_debug(0)
env.reset()

import matplotlib.pyplot as plt
from collections import Counter

def show_graghs(env, name):
    history = env.history

    plt.figure(figsize=(20, 8))

    data = [i['coverage'] for i in history]

    plt.subplot(221)
    plt.plot(data, marker='o', markersize=2, linewidth=1)
    plt.xlabel('step')
    plt.ylabel('coverage')
    plt.axhline(y=max(data), color='r', linewidth=1, linestyle='--')
    plt.text(0, max(data), str(max(data)), fontdict={'size': 8, 'color': 'r'})
    
    data = [i['action'] for i in history]
    ct = Counter(data)
    plt.subplot(222)
    plt.barh(list(ct.keys()), [ ct[k] for k in ct.keys() ])
    plt.yticks(range(env.mutate_size), 
               ['EraseBytes', 'InsertByte', 'InsertRepeatedBytes', 'ChangeByte', 'ChangeBit', 
                'ShuffleBytes', 'ChangeASCIIInteger', 'ChangeBinaryInteger', 'CopyPart'])
    plt.xlabel('step')

    data = [i['testcase'] for i in history]

    plt.subplot(223)
    plt.plot(data, marker='o', markersize=2, linewidth=1)
    plt.xlabel('step')
    plt.ylabel('len testcase')
    plt.axhline(y=max(data), color='r', linewidth=1, linestyle='--')
    plt.text(0, max(data), str(max(data)), fontdict={'size': 8, 'color': 'r'})
    
    data = [i['reward'] for i in history]
    plt.subplot(224)
    plt.plot(data, marker='o', markersize=2, linewidth=1)
    plt.xlabel('step')
    plt.ylabel('reward')
    plt.axhline(y=max(data), color='r', linewidth=1, linestyle='--')
    plt.text(0, max(data), str(max(data)), fontdict={'size': 8, 'color': 'r'})

    plt.savefig('{}_{}_{}.png'.format(ENV_NAME, TARGET, name))


import signal
def end(signum, handle):
    stop = timeit.default_timer()
    show_graghs(env, 'random-rlfuzz-envs')

    unique_path = len(env.unique_path)
    print('Total try: {}'.format(env.total_try))
    print('Max_coverage: {}'.format(sum(env.virgin_map)))
    print('Number of unique path: {}'.format(unique_path)) 
    print('Depth: {}'.format(env.depth))
    print('Total time: {}'.format(stop - start)) 
    print('Last find: {}'.format(env.last_find))
    exit(0)

signal.signal(signal.SIGINT, end)

# Random policy action for testing purposes
done = False
# numEpisodes = 10
# numMaxStepsPerEpisode = 100
mutator = ctfuzz.envs.fuzz_mutator.FuzzMutator(5)
# highest_reward = 0

start = timeit.default_timer()
print('Start time: {}'.format(start))

while not done:
    action = np.random.choice(mutator.Get_action_table_size())
    states, reward, done, info = env.step(action)
    # print('total-try: {}'.format(env.total_try))
    # highest_reward = max(highest_reward, reward)

# show_graghs(env, 'random')

# unique_path = len(env.unique_path)
# print('Total loop: {}'.format(total_try))
# print('Total try: {}'.format(env.total_try))
# print('Number of unique path: {}'.format(unique_path)) 
# print('Total time: {}'.format(stop - start)) 
