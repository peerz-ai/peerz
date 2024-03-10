# peerz

The peerz project enables efficient, distributed computing over a decentralized network, leveraging hivemind for peer discovery and communication. It consists of three main components:

- **Server**: Hosts and serves model computations.
- **Validator**: Validates servers and updates within the network.
- **Sequencer**: Ensures transaction consistency and order.

## Getting Started

### Prerequisites

- Python 3.8 or higher

### Installation

#### Automated Installation

You can install peerz directly using our installation script from GitHub. This method doesn't require manually cloning the repo:

```bash
curl -o- https://raw.githubusercontent.com/peerz-ai/peerz/main/scripts/install.sh | bash
```

This command downloads the `install.sh` script and executes it. The script sets up a Python virtual environment, installs necessary dependencies, and prepares peerz for use.

#### Manual Installation

If you prefer manual installation or need more control over the installation process, follow these steps:

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/peerz-ai/peerz.git
    cd peerz
    ```

2. **Set Up a Python Virtual Environment** (Optional, but recommended):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

4. **Install peerz**:
    ```bash
    pip install -e .
    ```

### Running peerz

After installation, you can start the Server, Validator, or Sequencer components using their respective scripts as described below. Ensure you activate the virtual environment if you set one up during manual installation.

## Running the Server

```bash
peerz server --converted_model_name_or_path <MODEL_PATH> --port <PORT> [--other_options]
```

## Running the Validator

```bash
peerz validator --initial_peers <PEER_ADDRESSES> --address <VALIDATOR_ADDRESS> --private_key <PRIVATE_KEY>
```

## Running the Sequencer

```bash
peerz sequencer --initial_peers <PEER_ADDRESSES> --address <SEQUENCER_ADDRESS> --private_key <PRIVATE_KEY>
```

## Configuration

For further customization, each component supports additional command-line arguments and can be configured via `config.yml`. Use the `-h` option for detailed usage instructions:

```bash
peerz server -h
peerz validator -h
peerz sequencer -h
```


<pre align="center">
                 .-^>>+~`                  
              -vkppqppppppw^               
            `xppx>-....`|?Kpp+             
           +ppx-          .+kpw            
          ~ppr    .|>>~     `upr           
          xpq.   ^qppppq|    |pp-          
         .ppw   .rppppppp    `kp?          
         .ppr    +rKpppppx+.  ?p?          
         .ppr    .-+???^?Kppu?...          
         .ppr             `?uppK?-         
     -vk|.ppr                `>zppp}~      
   +Kppq-.ppr                   .^rqpq?.   
 .zppv`  .ppr                      .^xpq~  
.upq~    .ppw                 ..      ?pp| 
?pp+   .?qpppu~            .vppppz`    ?pp.
upq    ?ppppppp`           ?ppppppp.   -pp^
upq    >ypppppp~         .^rppppppp`   `kp>
?pp^   .^vxKKx^       `>uppw?}xKky+    ?pp`
.upp|     ...      -?kppq}|. ..`.     >ppv 
 .wppw-         ~}qppkv~``          |xppv  
   +ypppw?>+>vxpppy?-  >kppz?^~~^?zpppu|   
     -?uqpppppkw>`     .`>wppppppppu?-     
         .....              .`--`.         
</pre>