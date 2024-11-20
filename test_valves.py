import os
from open_webui_workspace.screenpipe_function import Pipe as ScreenPipe
from open_webui_workspace.screenpipe_filter_function import Filter as ScreenFilter
from dotenv import load_dotenv

load_dotenv()

LLAMA_MODEL = "Llama-3.1-70B"
LOCAL_QWEN_MODEL = "qwen2.5-3b"
LLM_API_KEY = os.getenv("LLM_API_KEY")
if LLM_API_KEY is None:
    raise ValueError("LLM_API_KEY not set")

CUSTOM_FILTER_VALVES = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "LLM_API_KEY": LLM_API_KEY,
    "FORCE_TOOL_CALLING": False,
    "SCREENPIPE_SERVER_URL": "http://localhost:3030",
}

CUSTOM_PIPE_VALVES = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "LLM_API_KEY": LLM_API_KEY,
    "RESPONSE_MODEL": LLAMA_MODEL,
    "GET_RESPONSE": True,
}

OLLAMA_FILTER_VALVES = {
    "LLM_API_BASE_URL": "http://localhost:11434/v1",
    "LLM_API_KEY": "ollama-key",
    "FORCE_TOOL_CALLING": False,
    "SCREENPIPE_SERVER_URL": "http://localhost:3030",
}

OLLAMA_PIPE_VALVES = {
    "LLM_API_BASE_URL": "http://localhost:11434/v1",
    "LLM_API_KEY": "ollama-key",
    "RESPONSE_MODEL": "qwen2.5:3b",
    "GET_RESPONSE": False,
}

DEFAULT_PROMPT = "Search: limit of 2, type all. Task: Analyze the output and provide a summary. Search results may be incomplete."


def test_filter(prompt: str = DEFAULT_PROMPT, stream: bool = False):
    filter = ScreenFilter()
    pipe = ScreenPipe()
    # stream = False
    filter.valves = filter.Valves(**CUSTOM_FILTER_VALVES)
    pipe.valves = pipe.Valves(**CUSTOM_PIPE_VALVES)
    print("Filter valves:", filter.valves)
    print("Pipe valves:", pipe.valves)
    body = {"messages": [
        {"role": "user", "content": prompt}], "stream": stream}
    body = filter.inlet(body)
    print("Filter inlet complete. New user message:")
    print(body["messages"][-1]["content"])
    response = ""
    print("Pipe final messages:")
    if stream:
        for chunk in pipe.pipe(body):
            chunk_content = ""
            if isinstance(chunk, str):
                chunk_content = chunk
                print(chunk, end="", flush=True)
            elif chunk.choices[0].delta.content is not None:
                chunk_content = chunk.choices[0].delta.content
                print(chunk_content, end="", flush=True)
            else:
                finish_reason = chunk.choices[0].finish_reason
                # assert finish_reason is not None, "Finish reason must be present"
                print(f"\n\nFinish reason: {finish_reason}\n")
            response += chunk_content
        print()
    else:
        response = pipe.pipe(body)
        print("Pipe output:")
        print(response)
    body["messages"].append({"role": "assistant", "content": response})
    body = filter.outlet(body)
    final_message = body["messages"][-1]["content"]


def main(prompt: str = DEFAULT_PROMPT, stream: bool = True):
    test_filter(prompt=prompt, stream=stream)


if __name__ == "__main__":
    from sys import argv
    # TODO: Add arg for prompt
    if len(argv) > 1:
        test_filter(prompt=argv[1])
    else:
        test_filter()
