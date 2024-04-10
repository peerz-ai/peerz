from peerz.models.mixtral.block import WrappedMixtralBlock
from peerz.models.mixtral.config import DistributedMixtralConfig
from peerz.models.mixtral.model import (
    DistributedMixtralForCausalLM,
    DistributedMixtralForSequenceClassification,
    DistributedMixtralModel,
)
from peerz.utils.auto_config import register_model_classes

register_model_classes(
    config=DistributedMixtralConfig,
    model=DistributedMixtralModel,
    model_for_causal_lm=DistributedMixtralForCausalLM,
    model_for_sequence_classification=DistributedMixtralForSequenceClassification,
)
