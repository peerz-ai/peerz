from hivemind import DHT, get_logger
import time
from peerz.utils.signature import prepare_data_for_signing, sign_data
from peerz.validator.state_updater import StateUpdaterThread
from peerz.utils.consensus import contract

logger = get_logger(__name__)

contract = contract()

class Validator:
    def __init__(
        self,
        *,
        dht: DHT,
        updater: StateUpdaterThread,
        address: str,
        private_key: str,
        check_period: float = 20,
    ):
        self.dht = dht
        self.address = address
        self.private_key=private_key
        self.check_period = check_period
        self.updater = updater
    def run(self):
        while True:
            try:
                peerIds, contributions, total = prepare_data_for_signing(self.updater.state)
                # get the active peers
                (active_peers_length, contributions) = contract.functions.getActivePeers().call()
                print(active_peers_length, contributions)
                active_peers = contract.functions.getActivePeersRange(0, active_peers_length - 1).call()
                print(active_peers[0][0].hex())
                for i in range(active_peers_length):
                    should_get_reported = False
                    if active_peers[i][0].hex() in peerIds:
                        # get the index of the peerId
                        index = peerIds.index(active_peers[i][0].hex())
                        if contributions[index] != contributions[i]:
                            should_get_reported = True
                    else:
                        should_get_reported = True

                    if should_get_reported:
                        peerId = active_peers[i][0].hex()
                        signature_hex = sign_data(self.private_key, peerId)
                        # store the signature
                        self.dht.store(
                            key="_peerz.validators",
                            subkey=peerId,
                            value=dict(peerIds=peerIds, throughputs=throughputs, layers=layers, signature=signature),
                            expiration_time=get_dht_time() + 20,
                        )
                
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


