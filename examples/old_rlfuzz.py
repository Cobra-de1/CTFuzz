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
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Activation, Flatten, Input, Concatenate
from tensorflow.keras.optimizers import Adam

# pip install keras-rl2
from rl.agents import DDPGAgent
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess

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

ENV_NAME = 'OldRlfuzzEnv-v0'
env = gym.make(ENV_NAME)
env.set_target(target_path, target_args)

with open(seed_path, 'rb') as f:
    seed = f.read()    

env.add_seed(seed)

env.set_debug(0)
env.reset()

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
    print('Total time: {}'.format(stop - start)) 

    if not is_test:
        agent.save_weights('{}_{}_weights.h5f'.format(ENV_NAME, TARGET), overwrite=True)
        show_graghs(env, 'train')
    else:
        show_graghs(env, 'test')

    exit(0)

signal.signal(signal.SIGINT, end)

nb_actions = env.action_space.n
nb_observation = env.observation_space.shape[0]

actor_input = Input(shape=(1,) + env.observation_space.shape, name='actor_observation_input')
f_actor_input = Flatten()(actor_input)
x = Dense(1024, activation='relu')(f_actor_input)
x = Dense(128, activation='relu')(x)
y = Dense(nb_actions, activation='softmax')(x)
actor = Model(inputs=actor_input, outputs=y, name='Actor')
# actor.summary()

critic_action_input = Input(shape=(env.action_space.n), name='critic_action_input')
critic_observation_input = Input(shape=(1,) + env.observation_space.shape, name='critic_observation_input')
f_critic_observation_input = Flatten()(critic_observation_input)
x = Concatenate()([critic_action_input, f_critic_observation_input])
x = Dense(1024, activation='relu')(x)
x = Dense(128, activation='relu')(x)
y = Dense(1, activation='sigmoid')(x)
critic = Model(inputs=[critic_action_input, critic_observation_input], outputs=y, name='Critic')
# critic.summary()

agent = DDPGAgent(nb_actions=nb_actions, 
                  actor=actor, 
                  critic=critic, 
                  critic_action_input=critic_action_input, 
                  memory=SequentialMemory(limit=100000, window_length=1), 
                  nb_steps_warmup_critic=180, # 仅测试用
                  nb_steps_warmup_actor=180, 
                  random_process=OrnsteinUhlenbeckProcess(size=nb_actions, theta=.15, mu=0., sigma=.3), 
                  gamma=.99, 
                  target_model_update=1e-3
                 )
agent.compile(Adam(lr=.001, clipnorm=1.), metrics=['mae'])

if not is_test:
    start = timeit.default_timer()
    print('Start time: {}'.format(start))
    history = agent.fit(env, nb_steps=100000, visualize=False, verbose=0) # 执行nb_steps步，nb_max_episode_steps步后将done=True
    agent.save_weights('{}_{}_weights.h5f'.format(ENV_NAME, TARGET), overwrite=True)
else:
    agent.load_weights('{}_{}_weights.h5f'.format(ENV_NAME, TARGET))
    start = timeit.default_timer()
    print('Start time: {}'.format(start))
    agent.test(env, visualize=False, nb_max_episode_steps=20000000, nb_episodes=1)

end(0, 0)
