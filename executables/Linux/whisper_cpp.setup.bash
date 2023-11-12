#!/bin/bash

# GET USER PATH
get_user=$(who)
USER=${get_user%% *}
USER_HOME="/home/$USER"


# -- Edit bellow vvvv DeSOTA DEVELOPER EXAMPLe (C++ - Tool): Everything rely on Make file

# SETUP VARS
MODEL_NAME=WhisperCpp
# - Model Release
MODEL_RELEASE=https://github.com/franciscomvargas/whisper.cpp/archive/refs/tags/v0.0.0.zip
# - Model Path
#   $PWD = \home\[username]\Desota\Desota_Models\DeUrlCruncher\executables\Linux
MODEL_PATH=$USER_HOME/Desota/Desota_Models/$MODEL_NAME
# - Pre-Trained Model CMD
MODEL_PT_DOWNLD="$MODEL_PATH/models/download-ggml-model.sh base.en"



# SUPER USER DO > Required for DeRunner 
[ "$UID" -eq 0 ] || { 
    echo "Please consider running this script with root acess!"; 
    echo "Usage:"; 
    echo "sudo $0 [-m] [-q] [-h]";
    while true; do
        echo
        read -p " # Continue as user? [y|n]: " iknowhatamidoing
        case $iknowhatamidoing in
            [Yy]* ) break;;
            [Nn]* ) exit 1;;
            * ) echo "    Please answer yes or no.";;
        esac
    done
}

# IPUT ARGS - -s="Start Model Service"; -d="Print stuff and Pause at end"
manualstart=0
debug=0
while getopts mdhe: flag
do
    case $flag in
        m) manualstart=1;;
        d) debug=1;;
        h) { 
            echo "Usage:"; 
            echo "sudo $0 [-m] [-d] [-h]";
            echo "    -m = Start Service Manually";
            echo "    -d = Echo everything (debug)";
            echo "    -h = Help";
            echo "    [] = Optional";
            exit 1;
        };;
        ?) {
            echo "Usage:"; 
            echo "sudo $0 [-m] [-d] [-h]";
            echo "    -m = Start Service Manually";
            echo "    -d = Echo everything (debug)";
            echo "    -h = Help";
            echo "    [] = Optional";
            exit 1;
        };;
    esac
done
echo "Input Arguments:"
echo "    manualstart [-m]: $manualstart"
echo "    debug [-d]: $debug"

# >>Libraries required<<
echo "Step 0/3 - Check Required apt instalations"
echo "    libarchive-tools"
apt install libarchive-tools -y &>/dev/nul
echo "    libsdl2-dev"
apt-get install libsdl2-dev -y &>/dev/nul

# Move to Project Folder
if ( test -d "$MODEL_PATH" ); 
then
    cd $MODEL_PATH
else
    echo "Error:"
    echo "# Description: Model not installed correctly"
    echo "    expected_path = $MODEL_PATH"    
    # echo "DEV TIP:"
    # echo "# Download Release with this command:"
    # echo "    TODO"
    exit
fi

echo
echo "Step 1/3 - Download Pre-Trained Model"
bash $MODEL_PT_DOWNLD

echo
echo "Step 2/3 - Compile Project & Build main"
cd $MODEL_PATH
make

echo
echo "Step 3/3 - Build stream tool"
cd $MODEL_PATH
make stream


echo
echo
echo 'Setup Completed!'
# Start Model ?
if [ "$manualstart" -eq "0" ]; 
then
    $MODEL_PATH/stream -m $MODEL_PATH/models/ggml-base.en.bin -t 8 --step 500 --length 5000
fi
exit
