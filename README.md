# peerz

The peerz project facilitates distributed computing through a decentralized network, leveraging hivemind for peer discovery and communication. This project contains three main components:

- **Server**: Hosts and serves model computations.
- **Validator**: Validates servers and updates within the network.
- **Sequencer**: Sequences transactions to ensure consistency and order.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- PyTorch
- hivemind

### Installation

1. Clone this repository.
2. Install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

The server component hosts and serves computations. To start the server, use the `run_server` script.

```bash
peerz server --converted_model_name_or_path <MODEL_PATH> --port <PORT> [--other_options]
```

- `<MODEL_PATH>`: Path or name of the pretrained model.
- `<PORT>`: Port number for the server to listen on.

## Running the Validator

Validators validate transactions within the network. To start a validator, use the `run_validator` script.

```bash
peerz validator --initial_peers <PEER_ADDRESSES> --address <VALIDATOR_ADDRESS> --private_key <PRIVATE_KEY>
```

- `<PEER_ADDRESSES>`: Multiaddrs of initial peers in the DHT.
- `<VALIDATOR_ADDRESS>`: Address of the validator.
- `<PRIVATE_KEY>`: Private key of the validator.

## Running the Sequencer

Sequencers sequence transactions to maintain order and consistency. To start a sequencer, use the `run_sequencer` script.

```bash
peerz sequencer --initial_peers <PEER_ADDRESSES> --address <SEQUENCER_ADDRESS> --private_key <PRIVATE_KEY>
```

- `<PEER_ADDRESSES>`: Multiaddrs of initial peers in the DHT.
- `<SEQUENCER_ADDRESS>`: Address of the sequencer.
- `<PRIVATE_KEY>`: Private key of the sequencer.

## Configuration

Each component can be further configured through command-line arguments or a configuration file (`config.yml`). See the help (`-h`) option for each script for more details.

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