from llama_cpp import Llama

MODEL_PATH = r"C:\Users\yodah\.cache\lm-studio\models\hugging-quants\Llama-3.2-1B-Instruct-Q8_0-GGUF\llama-3.2-1b-instruct-q8_0.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,      # context window
    n_threads=8,     # adjust to your CPU
)

output = llm(
    "Q: What is an MCP server?\nA:",
    max_tokens=100,
    stop=["Q:"],
)

print(output["choices"][0]["text"])
