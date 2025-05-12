#!/usr/bin/python3
"""Script to cycle through available audio output devices
   Intended to run with a keyboard shortcut

This tool assumes use of pipewire (Won't work for Alsa/Wireplumber/PulseAudio)
"""
import subprocess
import os
import datetime
import sys

def log(msg):
    ext = os.getpid()
    if ext == "":
        ext = "out"

    dt = datetime.datetime.now().strftime("%F-%T")
    with open (f"/tmp/switch-audio.log.{ext}", "a+") as lf:
        print(f"{dt}\t{msg}", file=lf, flush=True)

def get_output_devices():
    """retuns a list of audio output device names"""
    result = []
    outputs = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
    if outputs.returncode != 0:
        log(f"Unable to fetch list of output devices: {outputs.stderr}")
        sys.exit(outputs.returncode)

    devices = outputs.stdout.split("\n")
    for dev in devices:
        if dev:
            name = dev.split()[1]
            result.append(name.strip())
    
    log(f"Available output devices: {result}")
    
    return result

def get_current_device():
    """returns the current selected audio output device name"""
    result = ""
    output = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True)
    result = output.stdout.strip()
    if result:
        log(f"Current device: {result}")
    else:
        log(f"Unable to fetch current output device: {output.stderr}")
        sys.exit(output.returncode)

    return result

def get_next_device(current):
    """given a current device name, return the next one in the list of outputs"""
    if not current:
        return 
    available_outputs = get_output_devices()
    if current in available_outputs:
        # fetch the index
        idx = available_outputs.index(current)
        next = (available_outputs*2)[idx+1]
        if next:
            log(f"Current device: {current}, Next: {next}")
        else:
            log(f"Unable to find the next output device from available list: {available_outputs}")
            sys.exit(1)

        return next

def switch_device(device):
    """switch output to the given device"""
    output = subprocess.run(["pactl", "set-default-sink", device], capture_output=False)
    success = output.returncode
    if output.returncode != 0:
        log(f"Unable to switch output device: {output.stderr}")
        sys.exit(output.returncode)
    else:
        log(f"Switched output device to: {device}")

def switch():
    curr = get_current_device()
    next = get_next_device(curr)
    switch_device(next)

if __name__ == "__main__":
    switch()

    
