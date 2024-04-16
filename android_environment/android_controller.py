import subprocess
import os

def execute_command(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print(f"Error executing {cmd}.")
    return None

def list_devices():
    ret = execute_command("adb devices")
    return list(map(lambda z: z.split()[0], ret.split("\n")[1:]))

class AndroidController:
    def __init__(self, device):
        self.device = device
        self.width, self.height = self.get_device_size()

    def get_device_size(self):
        ret = execute_command(f"adb -s {self.device} shell wm size")
        return map(int, ret.split(": ")[1].split("x"))

    def get_screenshot(self, path):
        return execute_command(f"adb -s {self.device} exec-out screencap -p > {path}")

    def get_xml(self, path):
        prefix = os.path.basename(path)
        dump = f"adb -s {self.device} shell uiautomator dump /sdcard/{prefix}"
        pull = f"adb -s {self.device} pull /sdcard/{prefix} {path}"
        execute_command(dump)
        return execute_command(pull)

    def back(self):
        return execute_command(f"adb -s {self.device} shell input keyevent KEYCODE_BACK")

    def tap(self, pos):
        return execute_command(f"adb -s {self.device} shell input tap {pos[0]} {pos[1]}")

    def touch_hold(self, pos, duration=1000):
        return execute_command(f"adb -s {self.device} shell input swipe {pos[0]} {pos[1]} {pos[0]} {pos[1]} {duration}")

    def swipe_point(self, pos, direction, length=2, duration=400):
        """
        Swipes on the screen, starting at pos and towards the given direction for the specified length and time duration.
        """

        # up, down, left, right
        dirs = [(0, -2), (0, 2), (-1, 0), (1, 0)]

        unit_sz = length * int(self.width / 10)
        offset = (pos[0] + unit_sz * dirs[direction][0] * length, pos[1] + unit_sz * dirs[direction][1] * length)
        return execute_command(f"adb -s {self.device} shell input swipe {pos[0]} {pos[1]} {offset[0]} {offset[1]} {duration}")

    def swipe_points(self, start, end, duration=400):
        """
        Swipes from start to end for the specified time duration.
        """
        return execute_command(f"adb -s {self.device} shell input swipe {start[0]} {start[1]} {end[0]} {end[1]} {duration}")

    def type(self, string):
        string = string.replace(" ", "%s")
        string = string.replace("'", "")
        return execute_command(f"adb -s {self.device} shell input text {string}")
