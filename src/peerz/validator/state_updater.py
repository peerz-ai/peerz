import datetime
import threading
import time
from dataclasses import asdict, is_dataclass
from enum import Enum

import hivemind
import simplejson

from peerz.constants import UPDATE_PERIOD
from peerz.validator.health import fetch_health_state, fetch_health_state2
from peerz.validator.metrics import get_prometheus_metrics

logger = hivemind.get_logger(__name__)


class StateUpdaterThread(threading.Thread):
    def __init__(self, dht: hivemind.DHT, initial_peers, **kwargs):
        super().__init__(**kwargs)
        self.dht = dht
        self.initial_peers = initial_peers
        self.state_json = None
        self.ready = threading.Event()

    def run(self):
        logger.info("StateUpdaterThread started")
        while True:
            start_time = time.perf_counter()
            try:
                self.state = fetch_health_state2(self.dht, self.initial_peers)
                print(self.state)

                self.ready.set()
                logger.info(f"Fetched new state in {time.perf_counter() - start_time:.1f} sec")
            except Exception:
                logger.error("Failed to update state:", exc_info=True)

            delay = UPDATE_PERIOD - (time.perf_counter() - start_time)
            if delay < 0:
                logger.warning("Update took more than update_period, consider increasing it")
            time.sleep(max(delay, 0))

    def is_healthy(self) -> bool:
        return self.ready.is_set()

    def shutdown(self):
        """
        Gracefully terminate the container, process-safe.
        Please note that terminating container otherwise (e.g. by killing processes) may result in zombie processes.
        If you did already cause a zombie outbreak, your only option is to kill them with -9 (SIGKILL).
        """
        self.ready.clear()
        logger.info("Updater Thread shut down successfully")


def json_default(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Enum):
        return value.name.lower()
    if isinstance(value, hivemind.PeerID):
        return value.to_base58()
    if isinstance(value, datetime.datetime):
        return value.timestamp()
    raise TypeError(f"Can't serialize {repr(value)}")
