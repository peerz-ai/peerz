from __future__ import annotations

import threading
import time
from typing import Dict, List

import hivemind
from hivemind import DHT, get_dht_time
from hivemind.utils.logging import get_logger
from transformers import PretrainedConfig

from peerz.constants import DTYPE_MAP
from peerz.data_structures import UID_DELIMITER, ModelInfo, ServerInfo, ServerState, parse_uid
from peerz.server.memory_cache import MemoryCache
from peerz.utils.dht import declare_active_modules, get_remote_module_infos
from peerz.utils.misc import get_size_in_bytes
from peerz.utils.ping import PingAggregator
from peerz.utils.random import sample_up_to

logger = get_logger(__name__)

class ModuleAnnouncerThread(threading.Thread):
    """Periodically announces that this container hosts the specified modules, visible to all DHT peers"""

    def __init__(
        self,
        module_uids: List[str],
        dht: DHT,
        server_info: ServerInfo,
        model_info: ModelInfo,
        *,
        block_config: PretrainedConfig,
        memory_cache: MemoryCache,
        update_period: float,
        expiration: float,
        max_pinged: int = 5,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.module_uids = module_uids
        self.dht = dht
        self.server_info = server_info
        self.model_info = model_info
        self.memory_cache = memory_cache

        self.bytes_per_token = block_config.hidden_size * get_size_in_bytes(DTYPE_MAP[server_info.torch_dtype])
        self.bytes_per_token //= block_config.num_key_value_groups

        self.update_period = update_period
        self.expiration = expiration
        self.trigger = threading.Event()

        self.dht_prefix = parse_uid(module_uids[0])[0]
        block_indices = [parse_uid(uid)[1] for uid in module_uids]
        self.server_info.start_block = min(block_indices)
        self.server_info.end_block = max(block_indices) + 1

        self.max_pinged = max_pinged
        self.next_uids = [
            f"{self.dht_prefix}{UID_DELIMITER}{i}"
            for i in range(self.server_info.start_block + 1, self.server_info.end_block + 1)
        ]
        self.ping_aggregator = PingAggregator(self.dht)

    def run(self) -> None:
        while True:
            start_time = time.perf_counter()

            self.server_info.cache_tokens_left = self.memory_cache.bytes_left // self.bytes_per_token
            if self.server_info.state != ServerState.OFFLINE:
                self._ping_next_servers()
                self.server_info.next_pings = {
                    peer_id.to_base58(): rtt for peer_id, rtt in self.ping_aggregator.to_dict().items()
                }
            else:
                self.server_info.next_pings = None  # No need to ping if we're disconnecting

            declare_active_modules(
                self.dht,
                self.module_uids,
                self.server_info,
                expiration_time=get_dht_time() + self.expiration,
            )
            if self.server_info.state == ServerState.OFFLINE:
                break
            if not self.dht_prefix.startswith("_"):  # Not private
                self.dht.store(
                    key="_peerz.models",
                    subkey=self.dht_prefix,
                    value=self.model_info.to_dict(),
                    expiration_time=get_dht_time() + self.expiration,
                )

            delay = self.update_period - (time.perf_counter() - start_time)
            if delay < 0:
                logger.warning(
                    f"Declaring blocks to DHT takes more than --update_period, consider increasing it (currently {self.update_period})"
                )
            self.trigger.wait(max(delay, 0))
            self.trigger.clear()

    def announce(self, state: ServerState) -> None:
        self.server_info.state = state
        self.trigger.set()
        if state == ServerState.OFFLINE:
            self.join()

    def _ping_next_servers(self) -> Dict[hivemind.PeerID, float]:
        module_infos = get_remote_module_infos(self.dht, self.next_uids, latest=True)
        middle_servers = {peer_id for info in module_infos[:-1] for peer_id in info.servers}
        pinged_servers = set(sample_up_to(middle_servers, self.max_pinged))
        pinged_servers.discard(self.dht.peer_id)
        # Sample servers hosting the block after the last one (most likely continuations) separately
        pinged_servers |= set(sample_up_to(module_infos[-1].servers, self.max_pinged))
        self.ping_aggregator.ping(list(pinged_servers))
