import warnings

warnings.warn(
    "peerz.dht_utils has been moved to peerz.utils.dht. This alias will be removed in Peerz 2.2.0+",
    DeprecationWarning,
    stacklevel=2,
)

from peerz.utils.dht import *
