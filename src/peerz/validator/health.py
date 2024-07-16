import datetime
import time
from collections import Counter
from contextlib import suppress
from dataclasses import asdict
from functools import partial

import hivemind
import numpy as np
from multiaddr import Multiaddr
from peerz.data_structures import UID_DELIMITER, ServerState
from peerz.utils.dht import compute_spans, get_remote_module_infos

from peerz.constants import UPDATE_PERIOD
from peerz.validator.data_structures import ModelInfo
from peerz.validator.p2p_utils import check_reachability_parallel, get_peers_ips, extract_peer_ip_info

logger = hivemind.get_logger(__name__)

def fetch_health_state(dht: hivemind.DHT, initial_peers) -> list:
    start_time = time.perf_counter()
    bootstrap_peer_ids = []
    for addr in initial_peers:
        peer_id = hivemind.PeerID.from_base58(Multiaddr(addr)["p2p"])
        if peer_id not in bootstrap_peer_ids:
            bootstrap_peer_ids.append(peer_id)

    # check reachability of bootstrap peers
    reach_infos = dht.run_coroutine(partial(check_reachability_parallel, bootstrap_peer_ids))

    models = []
    model_index = dht.get("_peerz.models", latest=True)
    if model_index is not None and isinstance(model_index.value, dict):
        custom_models = []
        for dht_prefix, model in model_index.value.items():
            with suppress(TypeError, ValueError):
                model_info = ModelInfo.from_dict(model.value)
                if model_info.repository is None or not model_info.repository.startswith("https://huggingface.co/"):
                    continue
                model_info.dht_prefix = dht_prefix
                model_info.official = False
                custom_models.append(model_info)
        
        models.extend(sorted(custom_models, key=lambda info: (-info.num_blocks, info.dht_prefix)))
    logger.info(f"Fetching info for models {[info.name for info in models]}")

    block_uids = [f"{model.dht_prefix}{UID_DELIMITER}{i}" for model in models for i in range(model.num_blocks)]
    module_infos = get_remote_module_infos(dht, block_uids, latest=True)

    model_servers = {}
    all_servers = {}
    offset = 0

    for model in models:
        model_servers[model.dht_prefix] = compute_spans(
            module_infos[offset : offset + model.num_blocks], min_state=ServerState.OFFLINE
        )
        all_servers.update(model_servers[model.dht_prefix])
        offset += model.num_blocks

    online_servers = [{
        "peer_id": peer_id,
        "throughput": round(span.server_info.throughput),
        "layers": span.server_info.end_block - span.server_info.start_block
    }  for peer_id, span in all_servers.items() if span.state == ServerState.ONLINE]
    
    return online_servers
