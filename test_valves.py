from open_webui_workspace.screenpipe_search_function import Pipe
from open_webui_workspace.simple_search_function import Pipe as SimplePipe
from utils.secrets import LLM_API_KEY
from dotenv import load_dotenv

load_dotenv()

CUSTOM_VALVES = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "LLM_API_KEY": LLM_API_KEY,
    "TOOL_MODEL": "Llama-3.1-70B",
    "FINAL_MODEL": "Qwen2.5-72B",
    "LOCAL_GRAMMAR_MODEL": "lmstudio-qwen2.5-14b",
    "USE_GRAMMAR": False,
    "SCREENPIPE_SERVER_URL": "http://localhost:3030"
}

DEFAULT_PROMPT = "Search with a limit of 1, type audio. Search results may be incomplete. Describe their contents regardless."

def main(prompt: str = DEFAULT_PROMPT, stream: bool = True): 
    pipe = Pipe()
    if isinstance(pipe, SimplePipe):
        stream = False
    # pipe.valves = pipe.Valves(**CUSTOM_VALVES)
    body = {"stream": stream, "messages": [
        {"role": "user", "content": prompt}]}
    if stream:
        chunk_count = 0
        for chunk in pipe.pipe(body):
            if chunk_count == 0:
                print("\nStreaming response:")
            chunk_count += 1
            if isinstance(chunk, str):
                print(chunk, end="", flush=True)
            elif chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)
            else:
                finish_reason = chunk.choices[0].finish_reason
                # assert finish_reason is not None, "Finish reason must be present"
                print(f"\n\nFinish reason: {finish_reason}\n\n")
    else:
        print("Non-streaming response:")
        print(pipe.pipe(body))

if __name__ == "__main__":
    from sys import argv
    # TODO: Add arg for prompt
    if len(argv) > 1:
        main(prompt=argv[1])
    else:
        main()
