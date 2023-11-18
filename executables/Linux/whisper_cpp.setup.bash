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
#   $PWD = /home/[username]/Desota/Desota_Models/WhisperCpp/executables/Linux
MODEL_PATH=$USER_HOME/Desota/Desota_Models/$MODEL_NAME
# - Pre-Trained Model CMD
PRE_MODEL_ID=base.en
PRE_MODEL_FILE=ggml-$PRE_MODEL_ID.bin
PRE_MODEL_QUANTIZE=ggml-$PRE_MODEL_ID-q5_0.bin
MODEL_PT_DOWNLD="$MODEL_PATH/models/download-ggml-model.sh $PRE_MODEL_ID"



# SUPER USER DO > Required for DeRunner 
[ "$UID" -eq 0 ] || { 
    echo "Please consider running this script with root access, to apt instalations!"; 
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
echo "Step 0/4 - Check Required apt instalations"
if [ "$debug" -eq "1" ]; 
then
    echo "    libarchive-tools"
    apt install libarchive-tools
    echo "    libsdl2-dev"
    apt-get install libsdl2-dev
    echo "    make"
    apt-get install make
    echo "    g++"
    apt-get install g++
    echo "    ffmpeg"
    apt install ffmpeg
else
    echo "    libarchive-tools"
    apt install libarchive-tools -y &>/dev/nul
    echo "    libsdl2-dev"
    apt-get install libsdl2-dev -y &>/dev/nul
    echo "    make"
    apt-get install make -y &>/dev/nul
    echo "    g++"
    apt-get install g++ -y &>/dev/nul
    echo "    ffmpeg"
    apt install ffmpeg -y &>/dev/nul
fi


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


if [ "$debug" -eq "1" ]; 
then    # DEBUG SETUP
    echo
    echo "Step 1/4 - Download Pre-Trained Model"
    echo "  ID: $MODEL_ID"
    bash $MODEL_PT_DOWNLD

    echo
    echo "Step 2/4 - Compile Project & Build main"
    echo "  Project: $MODEL_PATH"
    cd $MODEL_PATH
    make

    echo
    echo "Step 3/4 - Build quantize tool"
    cd $MODEL_PATH
    make quantize
    echo "  Quantize model: $PRE_MODEL_QUANTIZE"
    $MODEL_PATH/quantize $MODEL_PATH/models/$PRE_MODEL_FILE $MODEL_PATH/models/$PRE_MODEL_QUANTIZE q5_0

    echo
    echo "Step 4/4 - Build stream tool"
    cd $MODEL_PATH
    make stream
else    # QUIET SETUP
    echo
    echo "Step 1/4 - Download Pre-Trained Model"
    echo "  ID: $PRE_MODEL_ID"
    bash $MODEL_PT_DOWNLD &>/dev/nul

    echo
    echo "Step 2/4 - Compile Project & Build main"
    echo "  Project: $MODEL_PATH"
    cd $MODEL_PATH 
    make &>/dev/nul

    echo
    echo "Step 3/4 - Build quantize tool"
    cd $MODEL_PATH
    make quantize &>/dev/nul
    echo "  Quantize model: $PRE_MODEL_QUANTIZE"
    $MODEL_PATH/quantize $MODEL_PATH/models/ggml-base.en.bin $MODEL_PATH/models/$PRE_MODEL_QUANTIZE q5_0 &>/dev/nul

    echo
    echo "Step 4/4 - Build stream tool"
    cd $MODEL_PATH
    make stream &>/dev/nul
fi




echo
echo
echo 'Setup Completed!'
# Start Model ?
if [ "$manualstart" -eq "0" ]; 
then
    $MODEL_PATH/stream -m $MODEL_PATH/models/$PRE_MODEL_QUANTIZE --step 30000 --length 30000
fi
chown -R $USER $MODEL_PATH
exit
