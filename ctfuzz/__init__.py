import os

from gym.envs.registration import register

register(
    id='BaseEnv-v0',
    entry_point='ctfuzz.envs:FuzzBaseEnv',
)

register(
    id='CTFuzzEnv-v1',
    entry_point='ctfuzz.envs:CTFuzz1Env',
)

register(
    id='CTFuzzEnv-v2',
    entry_point='ctfuzz.envs:CTFuzz2Env',
)

register(
    id='OldRlfuzzEnv-v0',
    entry_point='ctfuzz.envs:OldRlfuzzEnv',
)