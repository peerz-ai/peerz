from hivemind import DHT, get_dht_time, get_logger
import time
import threading
from typing import List
from peerz.utils.signature import prepare_data_for_signing, sign_data

from peerz.validator.state_updater import StateUpdaterThread

logger = get_logger(__name__)

class Validator:
    def __init__(
        self,
        *,
        initial_peers: List[str],
        address: str,
        private_key: str,
        check_period: float = 20,
    ):
        logger.info("Connecting to DHT")
        self.dht = DHT(initial_peers, start=True)
        self.address = address
        self.private_key=private_key
        self.check_period = check_period
        self.updater = None
        self.initial_peers = initial_peers
        self.stop = threading.Event()
    def run(self):
        logger.info("Starting updater")
        self.updater = StateUpdaterThread(self.dht, daemon=True, initial_peers=self.initial_peers)
        self.updater.start()
        self.updater.ready.wait()
        while True:
            try:
                peerIds, throughputs, layers, total = prepare_data_for_signing(self.updater.state)
                signature_hex = sign_data(self.private_key, peerIds, throughputs, layers, total)
                print(peerIds, throughputs, layers, total, signature_hex)

                self.dht.store(
                    key="_peerz.validators",
                    subkey=self.address,
                    value=dict(peerIds=peerIds, throughputs=throughputs, layers=layers, signature=signature_hex),
                    expiration_time=get_dht_time() + 20,
                )
            except Exception:
                logger.error("Failed to update signature", exc_info=True)

            time.sleep(max(self.check_period, 0))


