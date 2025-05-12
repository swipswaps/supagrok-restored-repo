#!/usr/bin/env python3

from subprocess import run, PIPE

def run_gaze_recalibrate():
    """
    Runs the Supagrok gaze recalibration script and returns the output.
    """
    result = run(["python3", "/opt/supagrok/modules/gaze_recalibrate.py"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if result.returncode == 0:
        return result.stdout
    else:
        raise Exception(f"Gaze recalibration failed with error code {result.returncode}: {result.stderr}")

def run_alt_script():
    """
    Runs an alternative Supagrok script and returns the output.
    """
    result = run(["/opt/supagrok/modules/run_alt_script.sh"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if result.returncode == 0:
        return result.stdout
    else:
        raise Exception(f"Alternative script failed with error code {result.returncode}: {result.stderr}")

if __name__ == "__main__":
    try:
        print(run_gaze_recalibrate())
    except Exception as e:
        print(e)
        print(run_alt_script())