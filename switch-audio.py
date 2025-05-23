#!/usr/bin/python3
"""Script to cycle through available audio output devices
   Intended to run with a keyboard shortcut

This tool assumes use of pipewire (Won't work for Alsa/Wireplumber/PulseAudio)
"""
import subprocess
import os
import datetime
import sys
import argparse
import json



class Audio:
    class Device:
        """audio output device with all necessary details"""
        def __init__(self, dev:str):
            json_dev = dev
            if "index" in json_dev:
                self.index = json_dev["index"]
            if "name" in json_dev:
                self.name = json_dev["name"]
            if "description" in json_dev:
                self.description = json_dev["description"]
            if "properties" in json_dev:
                props = json_dev["properties"]
                if "object.serial" in props:
                    self.serial = props["object.serial"]
                if "device.id" in props:
                    self.deviceid = props["device.id"]
                if "device.nick" in props:
                    self.devicenick = props["device.nick"]
                if "device.description" in props:
                    self.devicedescription = props["device.description"]

    def log(self, msg):
        ext = os.getpid()
        if ext == "":
            ext = "out"

        dt = datetime.datetime.now().strftime("%F-%T")
        with open (f"/tmp/switch-audio.log.{ext}", "a+") as lf:
            print(f"{dt}\t{msg}", file=lf, flush=True)

    def __init__(self):
        command = "pactl"
        self.GET_SINK_CMD = f"{command} get-default-sink"
        self.SET_SINK_CMD = f"{command} set-default-sink"
        self.LIST_CMD = f"{command} --format=json list sinks"

    def run_command(self, cmd):
        """runs the command, returns a tuple of (exitcode, stdout, stderr)"""
        out = subprocess.run(cmd.split(), capture_output=True, text=True)
        if out.returncode != 0:
            self.log(f"{cmd} failed: {out.stderr}")

        return (out.returncode, out.stdout.strip())


    def get_output_devices(self):
        """retuns list of available audio output devices"""
        cmd = self.LIST_CMD
        retcode, out = self.run_command(cmd)
        if retcode != 0:
            sys.exit(retcode)

        devices = []
        output = json.loads(out)
        for item in output:
            dev = self.Device(item)
            devices.append(dev)

        self.log("Available output devices")
        for device in devices:
            self.log(f" |_ {device.serial}, {device.name}, {device.devicenick}")

        return devices


    def get_current_device(self):
        """returns the current selected audio output device name"""
        retcode, out = self.run_command(self.GET_SINK_CMD)
        if retcode != 0:
            sys.exit(retcode)

        self.log(f"Current device: {out}")

        return out

    def get_next_device(self, current):
        """given a current device name, return the next one in the list of outputs"""
        if not current:
            return
        available_outputs = self.get_output_devices()
        for idx, dev in enumerate(available_outputs):
            self.log(f"comparing {current} with {dev.name} ")
            if current == dev.name:
                next = (idx + 1) % len(available_outputs)
                self.log(f"Curent device: {dev.description}, Next: {available_outputs[next].description}")
                return available_outputs[next].name
        else:
            self.log(f"Unable to find next output device from available list: {[dev.name for dev in available_outputs]}")


    def switch_device(self, device):
        """switch output to the given device"""
        retcode, out = self.run_command(f"{self.SET_SINK_CMD} {device}")

        if retcode != 0:
            sys.exit(retcode)

        self.log(f"Switched output device to: {device}")


    def switch(self):
        curr = self.get_current_device()
        next = self.get_next_device(curr)
        self.switch_device(next)
        return next

def parse_args():
    parser = argparse.ArgumentParser(
        prog="switch-audio-device",
        description="Switch Audio Output Device",
        epilog="Running with arguments cycles through available output devices"
    )
    parser.add_argument('-v',
                        action="store_true",
                        default=False,
                        help="show current selected output")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()

    audio = Audio()
    if args.v:
        print(audio.get_current_device())
    else:
        dev = audio.switch()
        if sys.stdout and sys.stdout.isatty:
            print(f"Current output device: {dev}")
