from transformers import AutoTokenizer
from peerz import AutoDistributedModelForCausalLM
from peerz.constants import PUBLIC_INITIAL_PEERS
import sys

class Inference:
    def __init__(
        self,
        *,
        question: str,
    ):
        self.question = question
    def run(self):
        model_name = "bigscience/bloom-560m"  # This one is fine-tuned Llama 2 (70B)
        stop_sequence = "###"
        starting_text = "A chat between a curious human and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions."
        starting_text += stop_sequence + "Assistant: Hi! How can I help you?"
        starting_text += stop_sequence + "Human: "

        # Connect to a distributed network hosting model layers
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoDistributedModelForCausalLM.from_pretrained(model_name)

        with model.inference_session(max_length=100) as session:
            # Run the model as if it were on your computer
            input_text = starting_text + self.question + stop_sequence + "Assistant:"
            final_output = ""
            stop = False
            inputs = tokenizer(input_text, return_tensors="pt")["input_ids"]
            while not stop:
                outputs = model.generate(
                    inputs,
                    max_new_tokens=1,
                    # max_length=100,
                    session=session
                )
                inputs = None
                output = tokenizer.decode(outputs[0])
                # slice the input_text from the output if it is present
                if (output.startswith(input_text)):
                    output = output[len(input_text):]
                sys.stdout.write(output)
                if (output == stop_sequence):
                    stop = True
                final_output += output
            #print(final_output)
            #sys.stdout.write(final_output)
        """ inputs = tokenizer(input_text, return_tensors="pt")["input_ids"]
        outputs = model.generate(inputs, max_new_tokens=1)
        print(tokenizer.decode(outputs[0]))  # A cat sat on a mat... """