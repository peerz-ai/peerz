from peerz.models.falcon.block import WrappedFalconBlock
from peerz.models.falcon.config import DistributedFalconConfig
from peerz.models.falcon.model import (
    DistributedFalconForCausalLM,
    DistributedFalconForSequenceClassification,
    DistributedFalconModel,
)
from peerz.utils.auto_config import register_model_classes

register_model_classes(
    config=DistributedFalconConfig,
    model=DistributedFalconModel,
    model_for_causal_lm=DistributedFalconForCausalLM,
    model_for_sequence_classification=DistributedFalconForSequenceClassification,
)
