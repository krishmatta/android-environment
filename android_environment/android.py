import android_controller
import gym
import numpy as np
import tempfile
import xml.etree.ElementTree as ET
from gym import spaces
from PIL import Image

class AndroidEnv(gym.Env):
    def __init__(self, device, reward_fn, reset_cmds, app=None):
        self.device = device
        self.reward_fn = reward_fn # Takes as input an iterator of the log. Returns reward based on log.
        self.reset_cmds = reset_cmds # List of functions that take the android controller as input, ran when reset is called on environment.
        self.app = app
        self.android_controller = android_controller.AndroidController(self.device)

        self.reset()

        self.observation_space = spaces.Dict(
            {
                "image": spaces.Box(low=0, high=255, shape=(self.android_controller.width, self.android_controller.height, 3)),
                "posx": spaces.Box(low=0, high=self.android_controller.width, shape=(512, 0), dtype=np.int32), # TODO: Arbitrary size
                "posy": spaces.Box(low=0, high=self.android_controller.height, shape=(512, 0), dtype=np.int32)
            }
        )

        self.action_space = spaces.Dict(
            {
                "action_type": spaces.Discrete(6),
                "pos": spaces.Box(low=np.array([0, 0]), high=np.array([self.android_controller.width, self.android_controller.height]), dtype=np.int32),
                "direction": spaces.Discrete(4),
                "end": spaces.Box(low=np.array([0, 0]), high=np.array([self.android_controller.width, self.android_controller.height]), dtype=np.int32)
            }
        )

    def _get_device_size(self):
        return self.android_controller.get_device_size()

    def _get_obs(self):
        ret = {}

        # First get image
        f = tempfile.NamedTemporaryFile()
        path = f.name
        self.android_controller.get_screenshot(path)
        img = Image.open(path)
        ret["image"] = np.asarray(img)

        # Now get position of buttons
        f = open("temp.xml") # TODO: Fix this
        path = f.name
        self.android_controller.get_xml(path)
        tree = ET.parse(path)
        root = tree.getroot()
        stack = [root]
        posx = []
        posy = []
        while len(posx) < 512:
            if stack:
                curr = stack.pop()

                if 'bounds' in curr.attrib:
                    bound_left, bound_right = curr.attrib['bounds'].split('][')

                    bound_left = bound_left[1:]
                    bound_right = bound_right[:-1]

                    bound_left_x, bound_left_y = map(int, bound_left.split(','))
                    bound_right_x, bound_right_y = map(int, bound_right.split(','))

                    center_x = (bound_left_x + bound_right_x) // 2
                    center_y = (bound_left_y + bound_right_y) // 2

                    posx.append(center_x)
                    posy.append(center_y)

                stack.extend(list(curr))
            else:
                posx.append(0)
                posy.append(0)
        f.close()

        ret["posx"] = np.array(posx)
        ret["posy"] = np.array(posy)
        return ret

    def _get_reward(self):
        return self.reward_fn(self.android_controller.get_log())

    def reset(self):
        for reset_cmd in self.reset_cmds:
            reset_cmd(self.android_controller)
        if self.app:
            self.android_controller.open_app(self.app)
        return self._get_obs(), {}

    def step(self, action):
        # home, back, tap, touch_hold, swipe_point, swipe_points
        if action["action_type"] == 0 and not self.app: # Lock
            self.android_controller.home()
        elif action["action_type"] == 1 and not self.app: # Lock
            self.android_controller.back()
        elif action["action_type"] == 2:
            pos = tuple(action["pos"])
            self.android_controller.tap(pos)
        elif action["action_type"] == 3:
            pos = tuple(action["pos"])
            self.android_controller.touch_hold(pos)
        elif action["action_type"] == 4:
            pos = tuple(action["pos"])
            self.android_controller.swipe_point(pos, action["direction"])
        elif action["action_type"] == 5:
            start = tuple(action["pos"])
            end = tuple(action["end"])
            self.android_controller.swipe_points(start, end)

        observation = self._get_obs()
        reward = self._get_reward()
        terminated = False
        info = {}
        return observation, reward, terminated, False, info

    def render(self):
        return self._get_obs()["image"]
