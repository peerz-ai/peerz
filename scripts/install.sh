
#!/bin/bash
set -u

python="python"

abort() {
  printf "%s\n" "$1"
  exit 1
}

getc() {
  local save_state
  save_state=$(/bin/stty -g)
  /bin/stty raw -echo
  IFS= read -r -n 1 -d '' "$@"
  /bin/stty "$save_state"
}

exit_on_error() {
    exit_code=$1
    last_command=${@:2}
    if [ $exit_code -ne 0 ]; then
        >&2 echo "\"${last_command}\" command failed with exit code ${exit_code}."
        exit $exit_code
    fi
}

wait_for_user() {
  local c
  echo
  echo "Press RETURN to continue or any other key to abort"
  getc c
  # we test for \r and \n because some stuff does \r instead
  if ! [[ "$c" == $'\r' || "$c" == $'\n' ]]; then
    exit 1
  fi
}

shell_join() {
  local arg
  printf "%s" "$1"
  shift
  for arg in "$@"; do
    printf " "
    printf "%s" "${arg// /\ }"
  done
}

# string formatters
if [[ -t 1 ]]; then
  tty_escape() { printf "\033[%sm" "$1"; }
else
  tty_escape() { :; }
fi
tty_mkbold() { tty_escape "1;$1"; }
tty_underline="$(tty_escape "4;39")"
tty_blue="$(tty_mkbold 34)"
tty_red="$(tty_mkbold 31)"
tty_bold="$(tty_mkbold 39)"
tty_reset="$(tty_escape 0)"

ohai() {
  printf "${tty_blue}==>${tty_bold} %s${tty_reset}\n" "$(shell_join "$@")"
}

# Things can fail later if `pwd` doesn't exist.
# Also sudo prints a warning message for no good reason
cd "/usr" || exit 1

linux_install_pre() {
    sudo apt-get update 
    sudo apt-get install --no-install-recommends --no-install-suggests -y apt-utils curl git cmake build-essential
    exit_on_error $?
}

linux_install_python() {
    which $python
    if [[ $? != 0 ]] ; then
        ohai "Installing python"
        sudo apt-get install --no-install-recommends --no-install-suggests -y $python
    else
        ohai "Updating python"
        sudo apt-get install --only-upgrade $python
    fi
    exit_on_error $? 
    ohai "Installing python tools"
    sudo apt-get install --no-install-recommends --no-install-suggests -y $python-pip $python-dev 
    exit_on_error $? 
}

linux_update_pip() {
    PYTHONPATH=$(which $python)
    ohai "You are using python@ $PYTHONPATH$"
    ohai "Installing python tools"
    $python -m pip install --upgrade pip
}

linux_install_peerz() {
    ohai "Cloning peerz@main into ~/.peerz/peerz"
    mkdir -p ~/.peerz/peerz
    git clone git@github.com:peerz-ai/peerz.git ~/.peerz/peerz/ 2> /dev/null || (cd ~/.peerz/peerz/ ; git fetch origin main ; git checkout main ; git pull --ff-only ; git reset --hard ; git clean -xdf)
    ohai "Installing peerz"
    $python -m pip install -e ~/.peerz/peerz/
    exit_on_error $? 
}

linux_increase_ulimit(){
    ohai "Increasing ulimit to 1,000,000"
    prlimit --pid=$PPID --nofile=1000000
}


mac_install_xcode() {
    which -s xcode-select
    if [[ $? != 0 ]] ; then
        ohai "Installing xcode:"
        xcode-select --install
        exit_on_error $? 
    fi
}

mac_install_brew() {
    which -s brew
    if [[ $? != 0 ]] ; then
        ohai "Installing brew:"
        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    else
        ohai "Updating brew:"
        brew update --verbose
    fi
    exit_on_error $? 
}

mac_install_cmake() {
    which -s cmake
    if [[ $? != 0 ]] ; then
        ohai "Installing cmake:"
        brew install cmake
    else
        ohai "Updating cmake:"
        brew upgrade cmake
    fi
}

mac_install_python() {
    which -s python3
    ohai "Installing python3"
    brew list python@3 &>/dev/null || brew install python@3;
    ohai "Updating python3"
    brew upgrade python@3
    exit_on_error $? 
}

mac_update_pip() {
    PYTHONPATH=$(which $python)
    ohai "You are using python@ $PYTHONPATH$"
    ohai "Installing python tools"
    $python -m pip install --upgrade pip
}

mac_install_peerz() {
    ohai "Cloning peerz@main into ~/.peerz/peerz"
    mkdir -p ~/.peerz/peerz
    git clone git@github.com:peerz-ai/peerz.git ~/.peerz/peerz/ 2> /dev/null || (cd ~/.peerz/peerz/ ; git fetch origin main ; git checkout main ; git pull --ff-only ; git reset --hard; git clean -xdf)
    ohai "Installing peerz"
    $python -m pip install -e ~/.peerz/peerz/
    exit_on_error $? 
    deactivate
}

# Do install.
OS="$(uname)"
if [[ "$OS" == "Linux" ]]; then

    which -s apt
    if [[ $? == 0 ]] ; then
        abort "This linux based install requires apt. To run with other distros (centos, arch, etc), you will need to manually install the requirements"
    fi
    echo """
    
                 .-^>>+~'                  
              -vkppqppppppw^               
            'xppx>-....'|?Kpp+             
           +ppx-          .+kpw            
          ~ppr    .|>>~     'upr           
          xpq.   ^qppppq|    |pp-          
         .ppw   .rppppppp    'kp?          
         .ppr    +rKpppppx+.  ?p?          
         .ppr    .-+???^?Kppu?...          
         .ppr             '?uppK?-         
     -vk|.ppr                '>zppp}~      
   +Kppq-.ppr                   .^rqpq?.   
 .zppv'  .ppr                      .^xpq~  
.upq~    .ppw                 ..      ?pp| 
?pp+   .?qpppu~            .vppppz'    ?pp.
upq    ?ppppppp'           ?ppppppp.   -pp^
upq    >ypppppp~         .^rppppppp'   'kp>
?pp^   .^vxKKx^       '>uppw?}xKky+    ?pp'
.upp|     ...      -?kppq}|. ..'.     >ppv 
 .wppw-         ~}qppkv~'          |xppv  
   +ypppw?>+>vxpppy?-  >kppz?^~~^?zpppu|   
     -?uqpppppkw>'     .'>wppppppppu?-     
         .....              .'--'.         

    """
    ohai "This script will install:"
    echo "git"
    echo "curl"
    echo "cmake"
    echo "build-essential"
    echo "python3"
    echo "python3-pip"
    echo "peerz"

    wait_for_user
    linux_install_pre
    linux_install_python
    linux_update_pip
    linux_install_peerz

    ohai "Would you like to increase the ulimit? This will allow your miner to run for a longer time"
    wait_for_user
    linux_increase_ulimit
    echo ""
    echo ""
    echo "######################################################################"
    echo "##                                                                  ##"
    echo "##                          PEERZ SETUP                             ##"
    echo "##                                                                  ##"
    echo "######################################################################"
    echo ""
    echo ""

elif [[ "$OS" == "Darwin" ]]; then
    echo """
    
                 .-^>>+~'                  
              -vkppqppppppw^               
            'xppx>-....'|?Kpp+             
           +ppx-          .+kpw            
          ~ppr    .|>>~     'upr           
          xpq.   ^qppppq|    |pp-          
         .ppw   .rppppppp    'kp?          
         .ppr    +rKpppppx+.  ?p?          
         .ppr    .-+???^?Kppu?...          
         .ppr             '?uppK?-         
     -vk|.ppr                '>zppp}~      
   +Kppq-.ppr                   .^rqpq?.   
 .zppv'  .ppr                      .^xpq~  
.upq~    .ppw                 ..      ?pp| 
?pp+   .?qpppu~            .vppppz'    ?pp.
upq    ?ppppppp'           ?ppppppp.   -pp^
upq    >ypppppp~         .^rppppppp'   'kp>
?pp^   .^vxKKx^       '>uppw?}xKky+    ?pp'
.upp|     ...      -?kppq}|. ..'.     >ppv 
 .wppw-         ~}qppkv~'          |xppv  
   +ypppw?>+>vxpppy?-  >kppz?^~~^?zpppu|   
     -?uqpppppkw>'     .'>wppppppppu?-     
         .....              .'--'.         

    """
    ohai "This script will install:"
    echo "xcode"
    echo "homebrew"
    echo "git"
    echo "cmake"
    echo "python3"
    echo "python3-pip"
    echo "peerz"

    wait_for_user
    mac_install_brew
    mac_install_cmake
    mac_install_python
    mac_update_pip
    mac_install_peerz
    echo ""
    echo ""
    echo "######################################################################"
    echo "##                                                                  ##"
    echo "##                          PEERZ SETUP                             ##"
    echo "##                                                                  ##"
    echo "######################################################################"
else
  abort "peerz is only supported on macOS and Linux"
fi

# Use the shell's audible bell.
if [[ -t 1 ]]; then
printf "\a"
fi

echo ""
echo ""
ohai "Welcome. Installation successful"
