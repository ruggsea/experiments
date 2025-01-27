#!/usr/bin/env python3

# Set environment variables first
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"  # Using first 3 GPUs
os.environ["HF_HOME"] = "/data/.cache/huggingface"
os.environ["TRANSFORMERS_CACHE"] = "/data/.cache/huggingface"
os.environ["HF_DATASETS_CACHE"] = "/data/.cache/huggingface"
os.environ["WANDB_DIR"] = "/data/.cache"

# Create cache directory
os.makedirs("/data/.cache/huggingface", exist_ok=True)

import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    TrainerCallback,
    GenerationConfig,
)
from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model, PeftModel
from trl import SFTTrainer, SFTConfig, DataCollatorForCompletionOnlyLM
from trl.models.utils import unwrap_model_for_generation
import wandb
from datetime import datetime
import pandas as pd
import shutil
from huggingface_hub import HfApi
from dotenv import load_dotenv

load_dotenv()

# log in to hf
from huggingface_hub import login
login(token=os.getenv("HUGGING_FACE_API_KEY"))

def _generate_completion(model, tokenizer, prompt, generation_config, accelerator=None):
    # Tokenize prompt
    inputs = tokenizer(prompt, return_tensors="pt", padding=True)
    
    # Move to device and ensure correct dtype
    inputs = {k: v.to(dtype=torch.long if k == 'input_ids' else torch.bfloat16, device=model.device) for k, v in inputs.items()}

    # Generate with unwrapped model
    with unwrap_model_for_generation(model, accelerator) as unwrapped_model:
        unwrapped_model.eval()
        unwrapped_model = unwrapped_model.to(dtype=torch.bfloat16)
        
        with torch.no_grad():
            outputs = unwrapped_model.generate(
                **inputs,
                generation_config=generation_config,
            )
    
    # Decode and return only the generated part
    completion = tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
    return completion

class GenerationCallback(TrainerCallback):
    def __init__(self, trainer, tokenizer, steps=100):
        print("\nInitializing GenerationCallback...")
        self.trainer = trainer
        self.tokenizer = tokenizer
        self.steps = steps
        self.test_prompts = [
            "Prompt: What is machine learning?\n\nResponse A: ```Machine learning is a branch of artificial intelligence that enables computers to learn from data and improve their performance without being explicitly programmed.```\n\nResponse B: ```Machine learning uses statistical techniques to allow computers to find patterns in data.```\n\n",
            "Prompt: How does photosynthesis work?\n\nResponse A: ```Plants convert sunlight into energy```\n\nResponse B: ```Photosynthesis is the process where plants convert light energy into chemical energy using chlorophyll, water, and carbon dioxide to produce glucose and oxygen.```\n\n",
        ]
        self.generation_config = GenerationConfig(
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
        )
        self._last_logged_step = -1
        print("GenerationCallback initialized successfully")

    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step == self._last_logged_step:
            return

        if state.global_step % self.steps == 0:
            print(f"\nStep {state.global_step}: Running generation tests...")
            
            try:
                records = []
                
                for test_prompt in self.test_prompts:
                    # Format test message with chat template
                    test_messages = [
                        {
                            "role": "system",
                            "content": """Let's think step by step to judge which response is better for the given prompt. Please keep your thoughts clear and concise and at max around 300 words. The output should be in the following format:\n```## Rationale: <Your reasoning>\n## Winner: <model_a or model_b>```\n\n"""
                        },
                        {
                            "role": "user",
                            "content": test_prompt
                        }
                    ]
                    prompt = self.tokenizer.apply_chat_template(
                        test_messages,
                        tokenize=False
                    )

                    response = _generate_completion(
                        model=self.trainer.model,
                        tokenizer=self.tokenizer,
                        prompt=prompt,
                        generation_config=self.generation_config,
                        accelerator=self.trainer.accelerator
                    )
                    
                    records.append({
                        "prompt": test_prompt,
                        "response": response,
                        "step": state.global_step,
                        "epoch": state.epoch
                    })
                    
                    print(f"\nPrompt: {test_prompt}")
                    print(f"Response: {response}")
                
                predictions_df = pd.DataFrame.from_records(records)
                generation_table = wandb.Table(dataframe=predictions_df)
                
                wandb.log({
                    "generation_tests": generation_table,
                    "step": state.global_step
                })
                
                self._last_logged_step = state.global_step
                
            except Exception as e:
                print(f"Generation failed with error: {str(e)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                print("Stopping training due to generation failure")
                control.should_training_stop = True
                raise e
                
            finally:
                self.trainer.model.train()

def main():
    # Model and training parameters
    BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
    ADAPTER_MODEL = "agokrani/qwen-2.5-7b-wsdm-cot-7epochs"
    OUTPUT_DIR = "/data/models/qwen-7b-cot-wsdm-continued"
    HF_MODEL_ID = "ruggsea/qwen-2.5-7b-wsdm-cot-continued"

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Initialize wandb
    wandb.init(project="wsdm_cot_finetune_qwen7b_continued")
    
    # print visible devices
    print(f"Visible devices: {torch.cuda.device_count()}")

    # Quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL,
            trust_remote_code=True,
        )

        # Load dataset
        dataset = load_dataset("ruggsea/wsdm2024-deepseek-cot", split="train")
        
        def format_chat(example):
            messages = [
                {
                    "role": "system",
                    "content": """Let's think step by step to judge which response is better for the given prompt. Please keep your thoughts clear and concise and at max around 300 words. The output should be in the following format:\n```## Rationale: <Your reasoning>\n## Winner: <model_a or model_b>```\n\n"""
                },
                {
                    "role": "user",
                    "content": f"Prompt: {example['prompt']}\n\nResponse A: ```{example['response_a']}```\n\nResponse B: ```{example['response_b']}```\n\n"
                },
                {
                    "role": "assistant",
                    "content": f"## Rationale: {example['rationale']}\n## Winner: {example['winner']}"
                }
            ]
            return {
                "text": tokenizer.apply_chat_template(
                    messages,
                    tokenize=False
                ),
                "n_tokens": len(tokenizer.encode(tokenizer.apply_chat_template(
                    messages,
                    tokenize=False
                )))
            }
        
        # Process dataset
        processed_dataset = dataset.map(
            format_chat,
            remove_columns=dataset.column_names,
            num_proc=8
        )
        
        # Split into train/eval
        split_dataset = processed_dataset.train_test_split(test_size=0.05)
        train_dataset = split_dataset["train"]
        eval_dataset = split_dataset["test"]

        print(f"Number of training examples: {len(train_dataset)}")
        print(f"Number of validation examples: {len(eval_dataset)}")

        # First load model in bfloat16 without quantization
        print(f"Loading base model: {BASE_MODEL}")
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            attn_implementation="flash_attention_2"
        )

        # Load and merge adapter while still in bfloat16
        print(f"Loading and merging adapter: {ADAPTER_MODEL}")
        adapter_model = PeftModel.from_pretrained(model, ADAPTER_MODEL)
        model = adapter_model.merge_and_unload()

        # Now quantize the merged model to 4-bit
        print("Quantizing merged model to 4-bit...")
        model = AutoModelForCausalLM.from_pretrained(
            model.config._name_or_path,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            attn_implementation="flash_attention_2"
        )

        # Prepare model for training
        model.gradient_checkpointing_enable()
        model = prepare_model_for_kbit_training(model)

        # LoRA configuration
        peft_config = LoraConfig(
            lora_alpha=16,
            lora_dropout=0.1,
            r=8,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        )
        
        # make sure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Training arguments
        training_args = SFTConfig(
            output_dir=OUTPUT_DIR,
            num_train_epochs=7,
            per_device_train_batch_size=16,
            gradient_accumulation_steps=2,
            gradient_checkpointing=True,
            optim="paged_adamw_8bit",
            learning_rate=2e-5,  # One order of magnitude higher
            bf16=True,
            logging_steps=1,
            logging_dir="logs",
            save_strategy="epoch",
            eval_strategy="steps",
            eval_steps=500,
            do_eval=True,
            report_to="wandb",
            run_name=f"qwen-7b-cot-continued-{datetime.now().strftime('%Y-%m-%d-%H-%M')}",
            warmup_ratio=0.03,
            group_by_length=True,
            packing=False,
            weight_decay=0.01,
            max_grad_norm=0.3,
            lr_scheduler_type="linear",
            seed=3407,
        )

        # Initialize trainer with generation callback
        trainer = SFTTrainer(
            model=model,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            args=training_args,
            peft_config=peft_config,
        )
        
        generation_callback = GenerationCallback(trainer, tokenizer, steps=3000)
        trainer.add_callback(generation_callback)

        # Train
        print("Starting training...")
        model.config.use_cache = False
        trainer.train()
        
        # Save the final model
        print("Saving final model...")
        trainer.save_model()
        
        # Upload model to HuggingFace
        print(f"Uploading model to HuggingFace Hub: {HF_MODEL_ID}")
        api = HfApi()
        api.upload_folder(
            folder_path=OUTPUT_DIR,
            repo_id=HF_MODEL_ID,
            repo_type="model",
        )
        
        print("Training completed successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 