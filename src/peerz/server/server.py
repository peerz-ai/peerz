from __future__ import annotations

import gc
import math
import os
import random
import sys
import threading
import time
from typing import List, Optional, Sequence, Union

import psutil
import torch
import torch.mps
from hivemind import DHT, MAX_DHT_TIME_DISCREPANCY_SECONDS
from hivemind.moe.server.layers import add_custom_models_from_file
from hivemind.proto.runtime_pb2 import CompressionType
from hivemind.utils.logging import get_logger

import peerz
from peerz.constants import DTYPE_MAP, PUBLIC_INITIAL_PEERS
from peerz.data_structures import CHAIN_DELIMITER, UID_DELIMITER, ModelInfo, ServerInfo, ServerState
from peerz.server import block_selection
from peerz.server.block_utils import get_block_size, resolve_block_dtype
from peerz.server.reachability import ReachabilityProtocol, check_direct_reachability
from peerz.server.throughput import get_dtype_name, get_server_throughput
from peerz.utils.auto_config import AutoDistributedConfig
from peerz.utils.convert_block import QuantType, check_device_balance
from peerz.utils.dht import get_remote_module_infos
from peerz.utils.misc import get_size_in_bytes
from peerz.server.container import ModuleContainer

logger = get_logger(__name__)


class Server:
    """
    Runs ModuleContainer, periodically checks that the network is balanced,
    restarts the ModuleContainer with other layers if the imbalance is significant
    """

    def __init__(
        self,
        *,
        initial_peers: List[str],
        dht_prefix: Optional[str],
        converted_model_name_or_path: str,
        public_name: Optional[str] = None,
        throughput: Union[float, str],
        num_blocks: Optional[int] = None,
        block_indices: Optional[str] = None,
        num_handlers: int = 8,
        inference_max_length: Optional[int] = None,
        min_batch_size: int = 1,
        max_batch_size: Optional[int] = None,
        max_chunk_size_bytes: int = 256 * 1024 * 1024,
        max_alloc_timeout: float = 600,
        attn_cache_tokens: Optional[int] = None,
        torch_dtype: str = "auto",
        revision: Optional[str] = None,
        cache_dir: Optional[str] = None,
        max_disk_space: Optional[int] = None,
        device: Optional[Union[str, torch.device]] = None,
        compression=CompressionType.NONE,
        stats_report_interval: Optional[int] = None,
        custom_module_path=None,
        update_period: float = 60,
        expiration: Optional[float] = None,
        request_timeout: float = 3 * 60,
        session_timeout: float = 30 * 60,
        step_timeout: float = 5 * 60,
        prefetch_batches: int = 1,
        sender_threads: int = 1,
        balance_quality: float = 0.75,
        mean_balance_check_period: float = 120,
        mean_block_selection_delay: float = 5,
        token: Optional[Union[str, bool]] = None,
        quant_type: Optional[QuantType] = None,
        tensor_parallel_devices: Optional[Sequence[torch.device]] = None,
        skip_reachability_check: bool = False,
        reachable_via_relay: Optional[bool] = None,
        use_relay: bool = True,
        use_auto_relay: bool = True,
        adapters: Sequence[str] = (),
        **kwargs,
    ):
        """Create a server with one or more bloom blocks. See run_server.py for documentation."""

        self.converted_model_name_or_path = converted_model_name_or_path

        self.num_handlers = num_handlers
        self.compression = compression
        self.stats_report_interval, self.update_period = stats_report_interval, update_period
        self.prefetch_batches, self.sender_threads = prefetch_batches, sender_threads
        self.revision, self.token = revision, token

        if custom_module_path is not None:
            add_custom_models_from_file(custom_module_path)

        self.block_config = AutoDistributedConfig.from_pretrained(
            converted_model_name_or_path,
            use_auth_token=token,
            revision=revision,
        )

        if dht_prefix is None:
            dht_prefix = self.block_config.dht_prefix
        assert UID_DELIMITER not in dht_prefix and CHAIN_DELIMITER not in dht_prefix, (
            f"DHT prefix should not contain '{UID_DELIMITER}' or '{CHAIN_DELIMITER}'. "
            f"Please specify another --dht_prefix manually when starting a server"
        )
        self.dht_prefix = dht_prefix

        if expiration is None:
            expiration = max(2 * update_period, MAX_DHT_TIME_DISCREPANCY_SECONDS)
        self.expiration = expiration

        self.request_timeout = request_timeout
        self.session_timeout, self.step_timeout = session_timeout, step_timeout

        self.module_uids = [
            f"{self.dht_prefix}{UID_DELIMITER}{block_index}"
            for block_index in range(self.block_config.num_hidden_layers)
        ]

        if reachable_via_relay is None:
            is_reachable = check_direct_reachability(initial_peers=initial_peers, use_relay=False, **kwargs)
            reachable_via_relay = is_reachable is False  # if can't check reachability (returns None), run a full peer
            logger.info(f"This server is accessible {'via relays' if reachable_via_relay else 'directly'}")
        self.dht = DHT(
            initial_peers=initial_peers,
            start=True,
            num_workers=self.block_config.num_hidden_layers,
            use_relay=use_relay,
            use_auto_relay=use_auto_relay,
            client_mode=reachable_via_relay,
            **kwargs,
        )
        self.reachability_protocol = ReachabilityProtocol.attach_to_dht(self.dht) if not reachable_via_relay else None

        visible_maddrs_str = [str(a) for a in self.dht.get_visible_maddrs()]
        if initial_peers == PUBLIC_INITIAL_PEERS:
            logger.info("Connecting to the public swarm")
        else:
            logger.info(f"Connecting to a private swarm, initial peers: {initial_peers}")
        logger.info(f"Running a server on {visible_maddrs_str}")
        self.should_validate_reachability = not skip_reachability_check and initial_peers == PUBLIC_INITIAL_PEERS

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        device = torch.device(device)
        if device.type == "cuda" and device.index is None:
            device = torch.device(device.type, index=0)
        self.device = device

        torch_dtype = resolve_block_dtype(self.block_config, DTYPE_MAP[torch_dtype])
        if device.type == "cpu" and torch_dtype == torch.float16:
            raise ValueError(
                f"Type float16 is not supported on CPU. Please use --torch_dtype float32 or --torch_dtype bfloat16"
            )
        if device.type == "mps" and torch_dtype == torch.bfloat16:
            logger.warning(f"Type bfloat16 is not supported on MPS, using float16 instead")
            torch_dtype = torch.float16
        self.torch_dtype = torch_dtype

        if tensor_parallel_devices is None:
            tensor_parallel_devices = (device,)
        self.tensor_parallel_devices = tuple(map(torch.device, tensor_parallel_devices))
        if len(self.tensor_parallel_devices) > 1:
            logger.info(f"Model weights will be split between {', '.join(tensor_parallel_devices)}")
            check_device_balance(self.tensor_parallel_devices)

        if quant_type is None:
            quant_type = QuantType.NF4 if device.type == "cuda" else QuantType.NONE
        self.quant_type = quant_type
        logger.info(f"Model weights are loaded in {get_dtype_name(torch_dtype, quant_type)} format")

        is_multiquery_attn = self.block_config.num_key_value_groups > 1
        if max_batch_size is None:
            max_batch_size = 8192 if is_multiquery_attn else 2048
        if inference_max_length is None:
            inference_max_length = 8192 if is_multiquery_attn else 2048
        self.min_batch_size, self.max_batch_size = min_batch_size, max_batch_size
        self.inference_max_length = inference_max_length
        self.max_chunk_size_bytes = max_chunk_size_bytes
        self.max_alloc_timeout = max_alloc_timeout

        # For attention cache in GPU or RAM
        if attn_cache_tokens is None:
            attn_cache_tokens = 16384 if is_multiquery_attn else 4096
        cache_values_per_block = 2 * self.block_config.hidden_size * attn_cache_tokens
        cache_values_per_block //= self.block_config.num_key_value_groups
        self._cache_bytes_per_block = cache_values_per_block * get_size_in_bytes(self.torch_dtype)

        # For disk cache
        self.cache_dir = cache_dir
        self.max_disk_space = max_disk_space
        self.adapters = adapters

        assert num_blocks is None or block_indices is None, "Please specify num_blocks or block_indices, not both"
        if num_blocks is None and block_indices is None:
            num_blocks = self._choose_num_blocks()
        if num_blocks is not None:
            num_blocks = min(num_blocks, self.block_config.num_hidden_layers)
        if block_indices is not None:
            try:
                start_block, end_block = [int(index.strip()) for index in block_indices.split(":")]
            except Exception as e:
                raise ValueError(f"Failed to parse `--block_indices {block_indices}`, must be start:end (e.g. 0:18)")
            block_indices = range(start_block, end_block)
            num_blocks = len(block_indices)
        self.strict_block_indices, self.num_blocks = block_indices, num_blocks

        gib = 1024**3
        self.attn_cache_bytes = self._cache_bytes_per_block * num_blocks
        logger.info(f"Attention cache for all blocks will consume up to {self.attn_cache_bytes / gib:.2f} GiB")

        assert isinstance(throughput, float) or throughput in ["auto", "eval", "dry_run"]
        if throughput in ["auto", "eval", "dry_run"]:
            force_eval = throughput in ["eval", "dry_run"]
            throughput_info = get_server_throughput(
                converted_model_name_or_path,
                self.block_config,
                device,
                torch_dtype,
                num_blocks=num_blocks,
                quant_type=quant_type,
                tensor_parallel_devices=self.tensor_parallel_devices,
                reachable_via_relay=reachable_via_relay,
                force_eval=force_eval,
                cache_dir=cache_dir,
            )
            if throughput == "dry_run":
                logger.info("Finished estimating throughput, exiting")
                sys.exit(0)
        else:
            throughput_info = {"throughput": throughput}
        self.server_info = ServerInfo(
            state=ServerState.JOINING,
            public_name=public_name,
            version=peerz.__version__,
            adapters=tuple(adapters),
            torch_dtype=str(torch_dtype).replace("torch.", ""),
            quant_type=quant_type.name.lower(),
            using_relay=reachable_via_relay,
            **throughput_info,
        )
        self.model_info = ModelInfo(num_blocks=self.block_config.num_hidden_layers)
        if not os.path.isdir(converted_model_name_or_path):
            self.model_info.repository = "https://huggingface.co/" + converted_model_name_or_path

        self.balance_quality = balance_quality
        self.mean_balance_check_period = mean_balance_check_period
        self.mean_block_selection_delay = mean_block_selection_delay

        self.module_container = None
        self.stop = threading.Event()

    def _choose_num_blocks(self) -> int:
        assert self.device.type in ("cuda", "mps"), (
            "GPU is not available. If you want to run a CPU-only server, please specify --num_blocks. "
            "CPU-only servers in the public swarm are discouraged since they are much slower"
        )
        num_devices = len(self.tensor_parallel_devices) if self.tensor_parallel_devices else 1

        if num_devices > 1:
            assert self.device.type == "cuda", f"Tensor parallelism is not supported on {self.device.type.upper()}"
            memory_per_device = tuple(
                torch.cuda.get_device_properties(device).total_memory for device in self.tensor_parallel_devices
            )
            total_memory = min(memory_per_device) * num_devices
            if max(memory_per_device) / min(memory_per_device) > 1.5:
                raise ValueError(
                    "GPU devices have highly uneven memory, which makes tensor parallelism inefficient. "
                    "Please launch individual servers on each GPU or set --num_blocks manually to "
                    "override this exception."
                )
        elif self.device.type == "cuda":
            total_memory = torch.cuda.get_device_properties(self.device).total_memory
        else:
            total_memory = psutil.virtual_memory().total

        gib = 1024**3
        # Estimate of GPU memory used in rpc_backward (2 GiB for BLOOM, proportional for other models)
        autograd_memory = 2 * gib * num_devices / 14336 * self.block_config.hidden_size

        block_size = get_block_size(self.block_config, "memory", dtype=self.torch_dtype, quant_type=self.quant_type)
        total_memory_per_block = block_size + self._cache_bytes_per_block
        if self.adapters:
            # Delay import of peerz.utils.peft to avoid unnecessary import of bitsandbytes
            from peerz.utils.peft import estimate_adapter_memory_per_block

            total_memory_per_block += estimate_adapter_memory_per_block(
                self.block_config,
                self.torch_dtype,
                self.adapters,
                token=self.token,
                cache_dir=self.cache_dir,
                max_disk_space=self.max_disk_space,
            )

        num_blocks = math.floor((total_memory - autograd_memory) / total_memory_per_block)
        assert num_blocks >= 1, "Your GPU does not have enough memory to serve at least one block"

        num_blocks = min(num_blocks, self.block_config.num_hidden_layers)
        logger.info(
            f"Server will fill your GPU memory with {num_blocks} transformer blocks. "
            f"If you want to leave some free GPU memory, please specify a lesser --num_blocks manually"
        )
        return num_blocks

    def run(self):
        while True:
            block_indices = self._choose_blocks()
            self.module_container = ModuleContainer.create(
                dht=self.dht,
                dht_prefix=self.dht_prefix,
                converted_model_name_or_path=self.converted_model_name_or_path,
                block_config=self.block_config,
                attn_cache_bytes=self.attn_cache_bytes,
                server_info=self.server_info,
                model_info=self.model_info,
                block_indices=block_indices,
                num_handlers=self.num_handlers,
                min_batch_size=self.min_batch_size,
                max_batch_size=self.max_batch_size,
                max_chunk_size_bytes=self.max_chunk_size_bytes,
                max_alloc_timeout=self.max_alloc_timeout,
                inference_max_length=self.inference_max_length,
                torch_dtype=self.torch_dtype,
                cache_dir=self.cache_dir,
                max_disk_space=self.max_disk_space,
                device=self.device,
                compression=self.compression,
                stats_report_interval=self.stats_report_interval,
                update_period=self.update_period,
                expiration=self.expiration,
                request_timeout=self.request_timeout,
                session_timeout=self.session_timeout,
                step_timeout=self.step_timeout,
                prefetch_batches=self.prefetch_batches,
                sender_threads=self.sender_threads,
                revision=self.revision,
                token=self.token,
                quant_type=self.quant_type,
                tensor_parallel_devices=self.tensor_parallel_devices,
                should_validate_reachability=self.should_validate_reachability,
                start=True,
            )
            try:
                self.module_container.ready.wait()

                while True:
                    timeout = random.random() * 2 * self.mean_balance_check_period
                    if self.stop.wait(timeout):
                        return

                    if not self.module_container.is_healthy():
                        logger.warning("One of subprocesses crashed, restarting the server")
                        break

                    if self._should_choose_other_blocks():
                        logger.info("Swarm is imbalanced, server will load other blocks")
                        break  # Stop serving this set of modules
            finally:
                self.module_container.shutdown()

            self._clean_memory_and_fds()

    def _clean_memory_and_fds(self):
        self.module_container = None
        gc.collect()  # In particular, this closes unused file descriptors

        if self.device.type == "cuda":
            torch.cuda.empty_cache()

            allocated_vram = torch.cuda.memory_allocated(self.device)
            reserved_vram = torch.cuda.memory_reserved(self.device)
            gib = 1024**3
            logger.info(
                f"Cleaning up, left {allocated_vram / gib:.1f} GiB allocated memory, "
                f"{reserved_vram / gib:.1f} GiB reserved memory"
            )
        elif self.device.type == "mps":
            torch.mps.empty_cache()

    def _choose_blocks(self) -> List[int]:
        if self.strict_block_indices is not None:
            return self.strict_block_indices

        # If multiple servers (e.g., launched on the same machine by a script) get to this line at the same time,
        # this delay decreases the probability of a race condition while choosing the best blocks to serve.
        time.sleep(random.random() * 2 * self.mean_block_selection_delay)
        module_infos = get_remote_module_infos(self.dht, self.module_uids, latest=True)
        return block_selection.choose_best_blocks(self.num_blocks, module_infos)

    def _should_choose_other_blocks(self) -> bool:
        if self.strict_block_indices is not None:
            return False

        module_infos = get_remote_module_infos(self.dht, self.module_uids, latest=True)
        return block_selection.should_choose_other_blocks(self.dht.peer_id, module_infos, self.balance_quality)

    def shutdown(self, timeout: Optional[float] = 5):
        self.stop.set()
        if self.module_container is not None and self.module_container.is_alive():
            self.module_container.join(timeout)

        if self.reachability_protocol is not None:
            self.reachability_protocol.shutdown()
        self.dht.shutdown()
        self.dht.join()
