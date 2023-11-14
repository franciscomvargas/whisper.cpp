import os
import time
import requests
import yaml
from yaml.loader import SafeLoader
import json
import subprocess
import time
from runner_utils.utils import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-mr", "--model_req", 
                    help="DeSOTA Request as yaml file path",
                    type=str)
parser.add_argument("-mru", "--model_res_url",
                    help="DeSOTA API Rsponse URL for model results",
                    type=str)

# inspired inhttps://stackoverflow.com/a/13874620
def get_platform():
    _platform = sys.platform
    _win_res=["win32", "cygwin", "msys"]
    _lin_res=["linux", "linux2"]
    _user_sys = "win" if _platform in _win_res else "lin" if _platform in _lin_res else None
    if not _user_sys:
        raise EnvironmentError(f"Plataform `{_platform}` can not be parsed to DeSOTA Options: Windows={_win_res}; Linux={_lin_res}")
    return _user_sys
USER_SYS=get_platform()

# :: os.getcwd() = /home/[user]/Desota/Desota_Models/WhisperCpp
APP_PATH = os.path.dirname(os.path.realpath(__file__))

if USER_SYS == "win":
    USER_PATH = "\\".join(APP_PATH.split("\\")[:-3])
elif USER_SYS == "lin":
    USER_PATH = "/".join(APP_PATH.split("/")[:-3])

DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")

TMP_PATH = os.path.join(DESOTA_ROOT_PATH, "tmp")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
USER_CONF_PATH = os.path.join(CONFIG_PATH, "user.config.yaml")

# Utils
def user_chown(path):
    '''Remove root previleges for files and folders: Required for Linux'''
    if USER_SYS == "lin":
        #CURR_PATH=/home/[USER]/Desota/DeRunner
        USER=str(USER_PATH).split("/")[-1]
        os.system(f"chown -R {USER} {path}")
    return

# DeSOTA Funcs
def get_model_req(req_path):
    '''
    {
        "task_type": None,      # TASK VARS
        "task_model": None,
        "task_dep": None,
        "task_args": None,
        "task_id": None,
        "filename": None,       # FILE VARS
        "file_url": None,
        "text_prompt": None     # TXT VAR
    }
    '''
    if not os.path.isfile(req_path):
        exit(1)
    with open(req_path) as f:
        return yaml.load(f, Loader=SafeLoader)

#   > Grab User Configurations
def get_user_config() -> dict:
    if not os.path.isfile(USER_CONF_PATH):
        print(f" [USER_CONF] Not found-> {USER_CONF_PATH}")
        raise EnvironmentError()
    with open( USER_CONF_PATH ) as f_user:
        return yaml.load(f_user, Loader=SafeLoader)


def main(args):
    '''
    return codes:
    0 = SUCESS
    1 = INPUT ERROR
    2 = OUTPUT ERROR
    3 = API RESPONSE ERROR
    9 = REINSTALL MODEL (critical fail)
    '''

    #---INPUT---# TODO (PRO ARGS)
    #---INPUT---#

    # Time when grabed
    start_time = int(time.time())

    # DeSOTA Model Request
    model_request_dict = get_model_req(args.model_req)
    
    # API Response URL
    send_task_url = args.model_res_url
    
    # TMP File Path
    out_filepath = os.path.join(APP_PATH, f"speech-recognition{start_time}")
    
    # Get audio from request
    _req_audio = get_request_audio(model_request_dict, TMP_PATH)
    user_chown(_req_audio)
    # Audio Found!
    if _req_audio:
        _tmp_16b_conversion = os.path.join(APP_PATH, f"whisper_tmp{start_time}.wav")
        # Convert Audio to 16bit .wav file
        _conversion_res = os.system(f"ffmpeg -i {_req_audio} -ar 16000 -ac 1 -c:a pcm_s16le {_tmp_16b_conversion}")
        if _conversion_res != 0:
            print(f"[ ERROR ] -> Whisper Request Failed: File Conversion Error")
            for file in [_req_audio, _tmp_16b_conversion]:
                if os.path.isfile(file):
                    os.remove(file)
            exit(2)
        user_chown(_tmp_16b_conversion)
        # Run Model
        _main_path = os.path.join(APP_PATH, main)
        _sproc = subprocess.Popen([ 
            _main_path, 
            "-f",  _tmp_16b_conversion, 
            "--output-txt", "--output-file", out_filepath]
        )
        # TODO: implement model timeout
        while True:
            _ret_code = _sproc.poll()
            if _ret_code != None:
                break
        out_filepath += ".txt"
        user_chown(out_filepath)
    else:
        print(f"[ ERROR ] -> Whisper Request Failed: No Input found")
        exit(1)

    if not os.path.isfile(out_filepath):
        print(f"[ ERROR ] -> Whisper Request Failed: No Output found")
        exit(2)
    
    with open(out_filepath, "r") as fr:
        model_res = fr.read()

    print(f"[ INFO ] -> Whisper Response:{model_res}")
    
    # DeSOTA API Response Preparation
    files = []
    with open(out_filepath, 'rb') as fr:
        files.append(('upload[]', fr))
        # DeSOTA API Response Post
        send_task = requests.post(url = send_task_url, files=files)
        print(f"[ INFO ] -> DeSOTA API Upload:{json.dumps(send_task.json(), indent=2)}")
    # Delete temporary file
    for file in [_req_audio, _tmp_16b_conversion, out_filepath]:
        if os.path.isfile(file):
            os.remove(file)

    if send_task.status_code != 200:
        print(f"[ ERROR ] -> Whisper Post Failed (Info):\nfiles: {files}\nResponse Code: {send_task.status_code}")
        exit(3)
    
    print("TASK OK!")
    exit(0)


if __name__ == "__main__":
    args = parser.parse_args()
    if not args.model_req or not args.model_res_url:
        raise EnvironmentError()
    main(args)
