import os, sys
import time, re, json, shutil
import requests, subprocess
import yaml
from yaml.loader import SafeLoader

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-mr", "--model_req", 
                    help="DeSOTA Request as yaml file path",
                    type=str)
parser.add_argument("-mru", "--model_res_url",
                    help="DeSOTA API Result URL. Recognize path instead of url for desota tests", # check how is atribuited the dev_mode variable in main function
                    type=str)

DEBUG = False

# DeSOTA Funcs [START]
#   > Get User OS
# inspired inhttps://stackoverflow.com/a/13874620
def get_platform():
    _platform = sys.platform
    _win_res=["win32", "cygwin", "msys"]
    _lin_res=["linux", "linux2"]
    _user_sys = "win" if _platform in _win_res else "lin" if _platform in _lin_res else None
    if not _user_sys:
        raise EnvironmentError(f"Plataform `{_platform}` can not be parsed to DeSOTA Options: Windows={_win_res}; Linux={_lin_res}")
    return _user_sys
#   > Grab DeSOTA Paths
USER_SYS=get_platform()
APP_PATH = os.path.dirname(os.path.realpath(__file__))
#   > USER_PATH
if USER_SYS == "win":
    path_split = str(APP_PATH).split("\\")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "\\".join(path_split[:desota_idx])
elif USER_SYS == "lin":
    path_split = str(APP_PATH).split("/")
    desota_idx = [ps.lower() for ps in path_split].index("desota")
    USER=path_split[desota_idx-1]
    USER_PATH = "/".join(path_split[:desota_idx])
def user_chown(path):
    '''Remove root previleges for files and folders: Required for Linux'''
    if USER_SYS == "lin":
        #CURR_PATH=/home/[USER]/Desota/DeRunner
        os.system(f"chown -R {USER} {path}")
    return
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")

#   > Import DeSOTA Scripts
RUNNER_UTILS_DIR = os.path.join(APP_PATH, "runner_utils")
RUNNER_UTILS_PY = os.path.join(RUNNER_UTILS_DIR, "utils.py")
DERUNNER_UTILS_PATH = os.path.join(DESOTA_ROOT_PATH, "DeRunner", "Tools", "decode_desota_model_request.py")
RUNNER_UTILS_URL = "https://raw.githubusercontent.com/DeSOTAai/DeRunner/main/Tools/decode_desota_model_request.py"
_utils_init = os.path.join(RUNNER_UTILS_DIR, "__init__.py")
_desota_files = [RUNNER_UTILS_PY, _utils_init]
_desota_isfiles = [os.path.isfile(p) for p in _desota_files]
if False in _desota_isfiles:
    if not os.path.isdir(RUNNER_UTILS_DIR):
        os.mkdir(RUNNER_UTILS_DIR)
    if not os.path.isfile(_utils_init):
        open(_utils_init, 'w').close()
    if not os.path.isfile(RUNNER_UTILS_PY) and os.path.isfile(DERUNNER_UTILS_PATH):
        shutil.copyfile(DERUNNER_UTILS_PATH, RUNNER_UTILS_PY)
    if not os.path.isfile(RUNNER_UTILS_PY):
        runner_utils_req = requests.get(RUNNER_UTILS_URL)
        if runner_utils_req.status_code != 200:
            raise EnvironmentError(f"Unable to create Desota Runner Utils\n  from: {RUNNER_UTILS_URL}\n    to: {RUNNER_UTILS_PY}")
        with open(RUNNER_UTILS_PY, "w") as ru:
            ru.write(runner_utils_req.text)
    user_chown(RUNNER_UTILS_DIR)
from runner_utils.utils import *

#   > Parse DeSOTA Request
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
#   > FIND URL WITH REGEX
def get_url_from_str(string):
    # retrieved from https://www.geeksforgeeks.org/python-check-url-string/
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]
# DeSOTA Funcs [END]


def main(args):
    '''
    return codes:
    0 = SUCESS
    1 = INPUT ERROR
    2 = OUTPUT ERROR
    3 = API RESPONSE ERROR
    9 = REINSTALL MODEL (critical fail)
    '''
   # Time when grabed
    _report_start_time = time.time()
    start_time = int(_report_start_time)

    #---INPUT---# TODO (PRO ARGS)
    #---INPUT---#

    # DeSOTA Model Request
    model_request_dict = get_model_req(args.model_req)
    
    # API Response URL
    send_task_url = args.model_res_url
    
    # TARGET File Path
    out_filepath = os.path.join(APP_PATH, f"speech-recognition{start_time}")
    if len(get_url_from_str(send_task_url))>1:
        dev_mode = False
    else:
        dev_mode = True
        report_path = send_task_url

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
        _main_path = os.path.join(APP_PATH, "main")
        _model_path = os.path.join(APP_PATH, "models", "ggml-base.en-q5_0.bin")
        whisper_cmd = [ 
            _main_path,
            "-m", _model_path,
            "-f",  _tmp_16b_conversion, 
            "--output-txt", "--output-file", out_filepath
        ]
        print("WHISPER CMD:")
        print(" ".join(whisper_cmd))
        _sproc = subprocess.Popen(whisper_cmd)
        # TODO: implement model timeout
        while True:
            _ret_code = _sproc.poll()
            if _ret_code != None:
                break
        out_filepath += ".txt"
        print(out_filepath)
        user_chown(out_filepath)
    else:
        print(f"[ ERROR ] -> Whisper Request Failed: No Input found")
        exit(1)

    if not os.path.isfile(out_filepath):
        print(f"[ ERROR ] -> Whisper Request Failed: No Output found")
        exit(2)
    
    if dev_mode:
        if not report_path.endswith(".json"):
            report_path += ".json"
        with open(report_path, "w") as rw:
            json.dump(
                {
                    "Model Result Path": out_filepath,
                    "Processing Time": time.time() - _report_start_time
                },
                rw,
                indent=2
            )
        user_chown(report_path)
        user_chown(out_filepath)
        print(f"Path to report:\n\t{report_path}")
    else:
        with open(out_filepath, "r") as fr:
            model_res = fr.read()
        with open(out_filepath, "w") as fw:
            model_res = model_res.replace("\n", "<br>").replace("\t", "  ")
            fw.write(model_res)

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
