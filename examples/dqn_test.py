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

ENV_NAME = 'CTFuzzEnv-v2'
env = gym.make(ENV_NAME)
env.set_target(target_path, target_args)

with open(seed_path, 'rb') as f:
    seed = f.read()

env.add_seed([seed])

env.set_debug(0)
# env.reset()
is_test = int(sys.argv[2])

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

    unique_path = len(env.unique_path)
    print('Total try: {}'.format(env.total_try))
    print('Max_coverage: {}'.format(sum(env.virgin_map)))
    print('Number of unique path: {}'.format(unique_path)) 
    print('Depth: {}'.format(env.depth))
    print('Total time: {}'.format(stop - start)) 
    print('Last find: {}'.format(env.last_find)) 

    if not is_test:
        dqn.save_weights('{}_{}_weights.h5f'.format(ENV_NAME, TARGET), overwrite=True)
        show_graghs(env, 'train')
    else:
        show_graghs(env, 'test')
    
    exit(0)

signal.signal(signal.SIGINT, end)

states = env.observation_space.shape[0]
actions = env.action_space.n

def build_model(states, actions):
    model = Sequential() 
    model.add(Dense(1024, activation='relu', input_shape=(1, states)))
    model.add(BatchNormalization())
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dense(64, activation='relu')) 
    model.add(Dense(actions, activation='linear'))
    return model


model = build_model(states, actions)
model.summary()

def build_agent(model, actions):
    policy = EpsGreedyQPolicy(eps=0.7)
    test_policy = EpsGreedyQPolicy(eps=0.7)
    memory = SequentialMemory(limit=1000000, window_length=1)
    # dqn = DQNAgent(model=model, memory=memory, policy=policy, 
    #               nb_actions=actions, nb_steps_warmup=200, target_model_update=1e-3)
    dqn = DQNAgent(model=model, memory=memory, policy=policy, test_policy=test_policy,
                  nb_actions=actions, nb_steps_warmup=1000, target_model_update=1)
    dqn.gamma = 0.9
    return dqn

dqn = build_agent(model, actions)
dqn.compile(Adam(learning_rate=1e-3), metrics=['mae'])

if not is_test:
    start = timeit.default_timer()
    print('Start time: {}'.format(start))
    history = dqn.fit(env, nb_steps=10000000, visualize=False, verbose=0)
    dqn.save_weights('{}_{}_weights.h5f'.format(ENV_NAME, TARGET), overwrite=True)
else:
    dqn.load_weights('{}_{}_weights.h5f'.format(ENV_NAME, TARGET))
    start = timeit.default_timer()
    print('Start time: {}'.format(start))
    dqn.test(env, nb_episodes=1, nb_max_episode_steps=20000000, visualize=False, verbose=1)

end(0, 0)

