from open_webui_workspace.screenpipe_search_function import Pipe
from utils.secrets import LLM_API_KEY

CUSTOM_VALVES = {
    "LLM_API_BASE_URL": "http://localhost:4000/v1",
    "LLM_API_KEY": LLM_API_KEY,
    "TOOL_MODEL": "gpt-4o-mini",
    "FINAL_MODEL": "Qwen2.5-72B",
    "LOCAL_GRAMMAR_MODEL": "lmstudio-nemo",
    "USE_GRAMMAR": False,
    "SCREENPIPE_SERVER_URL": "http://localhost:3030"
}


if __name__ == "__main__":
    pipe = Pipe()
    pipe.valves = pipe.Valves(**CUSTOM_VALVES)
    stream = True
    body = {"stream": stream, "messages": [
        {"role": "user", "content": "Search with a limit of 1, type audio. Search results may be incomplete. Describe their contents regardless."}]}
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
