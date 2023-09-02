from peerz.models.llama.block import WrappedLlamaBlock
from peerz.models.llama.config import DistributedLlamaConfig
from peerz.models.llama.model import (
    DistributedLlamaForCausalLM,
    DistributedLlamaForSequenceClassification,
    DistributedLlamaModel,
)
from peerz.utils.auto_config import register_model_classes

register_model_classes(
    config=DistributedLlamaConfig,
    model=DistributedLlamaModel,
    model_for_causal_lm=DistributedLlamaForCausalLM,
    model_for_sequence_classification=DistributedLlamaForSequenceClassification,
)
