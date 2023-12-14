import os, sys
import time, re, json, shutil
import requests, subprocess
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
#   > Import DeSOTA Scripts
from desota import detools
#   > Grab DeSOTA Paths
USER_SYS = detools.get_platform()
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
DESOTA_ROOT_PATH = os.path.join(USER_PATH, "Desota")
TMP_PATH = os.path.join(DESOTA_ROOT_PATH, "tmp")
CONFIG_PATH = os.path.join(DESOTA_ROOT_PATH, "Configs")
SERV_CONF_PATH = os.path.join(CONFIG_PATH, "services.config.yaml")
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
    model_request_dict = detools.get_model_req(args.model_req)
    
    # API Response URL
    result_id = args.model_res_url
    
    # TARGET File Path
    out_files = []
    out_urls = detools.get_url_from_str(result_id)
    if len(out_urls)==0:
        dev_mode = True
        report_path = result_id
    else:
        dev_mode = False
        send_task_url = out_urls[0]

    # Get audio from request
    _req_audios = detools.get_request_audio(model_request_dict, TMP_PATH)
    # Audio Found!
    if _req_audios:
        for audio_cnt, req_audio in enumerate(_req_audios):
            detools.user_chown(req_audio)
            out_filepath = os.path.join(APP_PATH, f"speech-recognition_{audio_cnt}_{start_time}")
            _tmp_16b_conversion = os.path.join(APP_PATH, f"whisper_tmp{start_time}.wav")
            # Convert Audio to 16bit .wav file
            _conversion_res = os.system(f"ffmpeg -i {req_audio} -ar 16000 -ac 1 -c:a pcm_s16le {_tmp_16b_conversion}")
            if _conversion_res != 0:
                print(f"[ ERROR ] -> Whisper Request Failed: File Conversion Error")
                for file in [req_audio, _tmp_16b_conversion]:
                    if os.path.isfile(file):
                        os.remove(file)
                exit(2)
            detools.user_chown(_tmp_16b_conversion)

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
            out_files.append(out_filepath)
            detools.user_chown(out_filepath)
    else:
        print(f"[ ERROR ] -> Whisper Request Failed: No Input found")
        exit(1)

    for file in out_files:
        if not os.path.isfile(file):
            out_files.remove(file)
        else:
            detools.user_chown(file)
    if not out_files:
        print(f"[ ERROR ] -> Whisper Request Failed: No Output found")
        exit(2)
    
    if dev_mode:
        if not report_path.endswith(".json"):
            report_path += ".json"
        with open(report_path, "w") as rw:
            json.dump(
                {
                    "Model Result Paths": out_files,
                    "Processing Time": time.time() - _report_start_time
                },
                rw,
                indent=2
            )
        detools.user_chown(report_path)
        print(f"Path to report:\n\t{report_path}")
    else:
        whisper_res = ""
        for file in  out_files:
            file_basename = os.path.basename(file)
            file_extension = os.path.splitext(file)[1]
            whisper_res += f"File Name: {file_basename}{file_extension}<br>"

            with open(out_filepath, "r") as fr:
                model_res = fr.read().replace("\n", "<br>").replace("\t", "  ")
            whisper_res += f"{model_res}<br><br>"
        print(f"[ INFO ] -> Whisper Response:{whisper_res}")

        res_filepath = os.path.join(APP_PATH, f"speech-recognition{start_time}")
        with open(res_filepath, "w") as fw:
            fw.write(whisper_res)
        detools.user_chown(res_filepath)

        # DeSOTA API Response Preparation
        files = []
        with open(res_filepath, 'rb') as fr:
            files.append(('upload[]', fr))
            # DeSOTA API Response Post
            send_task = requests.post(url = send_task_url, files=files)
            print(f"[ INFO ] -> DeSOTA API Upload:{json.dumps(send_task.json(), indent=2)}")

        # Delete temporary file
        tmp_files = out_files + [res_filepath]
        for file in tmp_files:
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
