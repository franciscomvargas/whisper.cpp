#!/bin/bash

# GET USER PATH
get_user=$(who)
USER=${get_user%% *}
USER_HOME="/home/$USER"



# -- Edit bellow vvvv DeSOTA DEVELOPER EXAMPLe (C++ - Tool): Everything rely on Make file

# Setup VARS
MODEL_NAME=WhisperCpp
# - Model Path
MODEL_PATH=$USER_HOME/Desota/Desota_Models/$MODEL_NAME



# -- https://youtu.be/5NV6Rdv1a3I -- 

# IPUT ARGS: -q="Quiet uninstall"; -p="User Password"
quiet=0
automatic=0
while getopts qahe: flag
do
    case $flag in
        q)  quiet=1;;
        a)  automatic=1;;
        h)  { 
            echo "Usage:"; 
            echo "sudo $0 [-q] [-a] [-h]";
            echo "    -q = Hands Free (quiet)";
            echo "    -a = DeSOTA automatic Uninstall"
            echo "    -h = Help";
            echo "    [] = Optional";
            exit 1;
        };;
        ?)  { 
            echo "Usage:"; 
            echo "sudo $0 [-q] [-a] [-h]";
            echo "    -q = Hands Free (quiet)";
            echo "    -a = DeSOTA automatic Uninstall"
            echo "    -h = Help";
            echo "    [] = Optional";
            exit 1;
        };;
    esac
done

# Copy File from future  deleted folder
SCRIPTPATH=$(realpath -s "$0")
BASENAME=$(basename $SCRIPTPATH)
if [ "$SCRIPTPATH" = "$USER_HOME/$BASENAME" ] || [ "$automatic" -eq "1" ];
then
    echo "Input Arguments:"
    echo "    quiet [-q]: $quiet"
    echo "    automatic [-a]: $automatic"
fi
if [ "$SCRIPTPATH" != "$USER_HOME/$BASENAME" ] && [ "$automatic" -eq "0" ];
then
    # SUPER USER RIGHTS
    [ "$UID" -eq 0 ] || { 
        echo "Please consider running this script with root, miniconda can require it!"; 
        echo "Usage:"; 
        echo "sudo $0 [-q] [-h]";
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

    if ( test -e "$USER_HOME/$BASENAME" ); then
        rm -rf $USER_HOME/$BASENAME
    fi
    cp $SCRIPTPATH $USER_HOME/$BASENAME
    #chown -R $USER $USER_HOME/$BASENAME
    if [ "$quiet" -eq "0" ]; then
        /bin/bash $USER_HOME/$BASENAME
    else
        /bin/bash $USER_HOME/$BASENAME -q
    fi
    exit
fi

if [ "$quiet" -eq "0" ]; 
then
    
    # DELETE PROJECT
    echo
    echo "Deleting permanently Project..."
    echo "    Project path: $MODEL_PATH"
    chown -R $USER $MODEL_PATH &>/dev/nul
    rm -r $MODEL_PATH
else

    # DELETE PROJECT
    echo
    echo "Deleting recursively Project..."
    echo "    Project path: $MODEL_PATH"
    chown -R $USER $MODEL_PATH &>/dev/nul
    rm -rf $MODEL_PATH
fi

if ( test -d "$MODEL_PATH" ); then
    echo 'Uninstall Fail'
    echo ">DEV TIP< Delete this folder:"
    echo "    $MODEL_PATH"
else
    echo
    echo
    echo 'Uninstalation Completed!'
fi

if [ "$automatic" -eq "0" ];
then
    rm -rf $USER_HOME/$BASENAME && exit
fi
exit
