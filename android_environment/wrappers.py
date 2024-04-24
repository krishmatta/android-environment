import copy
import numpy as np
import gym
from gym import spaces

class DiscreteWrapper(gym.Env):
    def __init__(self, env, m, n):
        self._env = env
        self.m = m # Num of rows
        self.n = n # Num of column

        self.action_space = spaces.Dict(
            {
                "action_type": spaces.Discrete(6),
                "pos": spaces.Box(low=np.array([0, 0]), high=np.array([m, n]), dtype=np.int32),
                "direction": spaces.Discrete(4),
                "end": spaces.Box(low=np.array([0, 0]), high=np.array([m, n]), dtype=np.int32)
            }
        )

    def reset(self):
        return self._env.reset()

    def _conv_pos(self, i, j):
        w, h = self._env._get_device_size()

        u = (i / self.m) * h
        d = ((i + 1) / self.m) * h
        cy = (u + d) // 2

        l = (j / self.n) * w
        r = ((j + 1) / self.n) * w
        cx = (l + r) // 2
        return (cx, cy)

    def step(self, action):
        action = copy.deepcopy(action)
        if "pos" in action:
            action["pos"] = self._conv_pos(*action["pos"])
        if "end" in action:
            action["end"] = self._conv_pos(*action["end"])
        return self._env.step(action)

    def render(self):
        return self._env.render()
