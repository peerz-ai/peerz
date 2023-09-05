# peerz

The peerz project facilitates distributed computing through a decentralized network, leveraging hivemind for peer discovery and communication. This project contains three main components:

- **Server**: Hosts and serves model computations.

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
python -m peerz.cli.run_server --converted_model_name_or_path <MODEL_PATH> --port <PORT> [--other_options]
```

- `<MODEL_PATH>`: Path or name of the pretrained model.
- `<PORT>`: Port number for the server to listen on.
