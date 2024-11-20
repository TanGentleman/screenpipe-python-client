###############################################################################
#
#  Welcome to Baml! To use this generated code, please run the following:
#
#  $ pip install baml
#
###############################################################################

# This file was generated by BAML: please do not edit it. Instead, edit the
# BAML files and re-generate this code.
#
# ruff: noqa: E501,F401
# flake8: noqa: E501,F401
# pylint: disable=unused-import,line-too-long
# fmt: off

file_map = {
    
    "clients.baml": "// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview\n\nclient<llm> OllamaQwen {\n  provider ollama\n  options {\n    model \"qwen2.5-coder:latest\"\n    base_url \"http://localhost:11434/v1\"\n    api_key ollama-key\n  }\n}\n\nclient<llm> GeminiFlash {\n  provider openai\n  options {\n    model \"openrouter/google/gemini-flash-1.5-8b\"\n    base_url \"http://localhost:4000/v1\"\n    api_key env.LLM_API_KEY\n  }\n}\n\n\nclient<llm> CustomGPT4o {\n  provider openai\n  options {\n    model \"gpt-4o\"\n    api_key env.OPENAI_API_KEY\n  }\n}\n\nclient<llm> CustomGPT4oMini {\n  provider openai\n  retry_policy Exponential\n  options {\n    model \"gpt-4o-mini\"\n    api_key env.OPENAI_API_KEY\n  }\n}\n\nclient<llm> CustomSonnet {\n  provider anthropic\n  options {\n    model \"claude-3-5-sonnet-20241022\"\n    api_key env.ANTHROPIC_API_KEY\n  }\n}\n\n\nclient<llm> CustomHaiku {\n  provider anthropic\n  retry_policy Constant\n  options {\n    model \"claude-3-haiku-20240307\"\n    api_key env.ANTHROPIC_API_KEY\n  }\n}\n\n// https://docs.boundaryml.com/docs/snippets/clients/round-robin\nclient<llm> CustomFast {\n  provider round-robin\n  options {\n    // This will alternate between the two clients\n    strategy [CustomGPT4oMini, CustomHaiku]\n  }\n}\n\n// https://docs.boundaryml.com/docs/snippets/clients/fallback\nclient<llm> OpenaiFallback {\n  provider fallback\n  options {\n    // This will try the clients in order until one succeeds\n    strategy [CustomGPT4oMini, CustomGPT4oMini]\n  }\n}\n\n// https://docs.boundaryml.com/docs/snippets/clients/retry\nretry_policy Constant {\n  max_retries 3\n  // Strategy is optional\n  strategy {\n    type constant_delay\n    delay_ms 200\n  }\n}\n\nretry_policy Exponential {\n  max_retries 2\n  // Strategy is optional\n  strategy {\n    type exponential_backoff\n    delay_ms 300\n    mutliplier 1.5\n    max_delay_ms 10000\n  }\n}",
    "generators.baml": "// This helps use auto generate libraries you can use in the language of\n// your choice. You can have multiple generators if you use multiple languages.\n// Just ensure that the output_dir is different for each generator.\ngenerator target {\n    // Valid values: \"python/pydantic\", \"typescript\", \"ruby/sorbet\", \"rest/openapi\"\n    output_type \"python/pydantic\"\n\n    // Where the generated code will be saved (relative to baml_src/)\n    output_dir \"../\"\n\n    // The version of the BAML package you have installed (e.g. same version as your baml-py or @boundaryml/baml).\n    // The BAML VSCode extension version should also match this version.\n    version \"0.67.0\"\n\n    // Valid values: \"sync\", \"async\"\n    // This controls what `b.FunctionName()` will be (sync or async).\n    default_client_mode sync\n}\n",
    "search.baml": "class TimeRange {\n  from_time string @description(\"ISO timestamp to filter results after this time\")\n  to_time string @description(\"ISO timestamp to filter results before this time\")\n}\n\nclass SearchParameters {\n  content_type \"OCR\" | \"AUDIO\" | \"ALL\" @description(\"Type of content to search for, defaults to ALL\")\n  time_range TimeRange? @description(\"Time range to filter results\")\n  limit int? @description(\"Maximum number of results to return\")\n  search_substring string? @description(\"Optional substring to filter text content\")\n  application string? @description(\"Optional filter to only show results from this application\")\n}\n\n// class SearchParameters {\n//   content_type \"OCR\" | \"AUDIO\" | \"ALL\" @description(\"Type of content to search for, defaults to ALL\")\n//   from_time string? @description(\"ISO timestamp to filter results after this time\")\n//   to_time string? @description(\"ISO timestamp to filter results before this time\")\n//   limit int? @description(\"Maximum number of results to return\")\n//   search_substring string? @description(\"Optional substring to filter text content\")\n//   application string? @description(\"Optional filter to only show results from this application\")\n// }\n\n// Function to construct search parameters from a natural language query\nfunction ConstructSearch(query: string, current_iso_timestamp: string) -> SearchParameters {\n  client OllamaQwen\n  prompt #\"\n    Let's construct a search request step by step:\n    1) What type of content is being requested (OCR, AUDIO, ALL)?\n    2) Is there a specific time range mentioned? If recent/today/etc, use last 2 days. Otherwise, leave null.\n    3) Should we limit the number of results?\n    4) Has the user asked to filter for a specific word?\n    5) Is a specific application mentioned?\n\n    Based on the query: \"{{ query }}\"\n    Current time: {{ current_iso_timestamp }}\n\n    {{ ctx.output_format }}\n  \"#\n}\n\n// Test the search construction\ntest basic_search {\n  functions [ConstructSearch]\n  args {\n    query #\"\n      I want to search for all audio content from the last 2 days.\n    \"#\n    current_iso_timestamp #\"2024-11-19T12:00:00Z\"#\n  }\n}\n\ntest search_with_substring {\n  functions [ConstructSearch]\n  args {\n    query #\"\n      Find OCR content containing the word 'invoice' from the last week\n    \"#\n    current_iso_timestamp #\"2024-11-19T15:30:00Z\"#\n  }\n}\n\ntest search_with_application {\n  functions [ConstructSearch]\n  args {\n    query #\"\n      Analyze my activity this month from the app Discord\n    \"#\n    current_iso_timestamp #\"2024-11-19T15:30:00Z\"#\n  }\n}\n\n\ntest search_with_limit {\n  functions [ConstructSearch]\n  args {\n    query #\"\n      Get the last 5 audio recordings\n    \"#\n    current_iso_timestamp #\"2024-11-19T15:30:00Z\"#\n  }\n}\n\ntest complex_search {\n  functions [ConstructSearch]\n  args {\n    query #\"\n      Analyze my screen activity from yesterday using the last 30 OCR results from the app Cursor\n    \"#\n    current_iso_timestamp #\"2024-11-19T15:30:00Z\"#\n  }\n}\n\n// NOTE, below from: https://github.com/BoundaryML/baml/blob/canary/fern/01-guide/06-prompt-engineering/chain-of-thought.mdx\n// Example\n// class Email {\n//     subject string\n//     body string\n//     from_address string\n// }\n\n\n// class OrderInfo {\n//     order_status \"ORDERED\" | \"SHIPPED\" | \"DELIVERED\" | \"CANCELLED\"\n//     tracking_number string?\n//     estimated_arrival_date string?\n// }\n\n// function GetOrderInfo(email: Email) -> OrderInfo {\n//   client OllamaQwen\n//   prompt #\"\n//     Extract the info from this email in the INPUT:\n\n//     INPUT:\n//     -------\n//     from: {{email.from_address}}\n//     Email Subject: {{email.subject}}\n//     Email Body: {{email.body}}\n//     -------\n\n//     {{ ctx.output_format }}\n\n//     Before you output the JSON, please explain your\n//     reasoning step-by-step. Here is an example on how to do this:\n//     'If we think step by step we can see that ...\n//      therefore the output JSON is:\n//     {\n//       ... the json schema ...\n//     }'\n//   \"#\n// }\n\n// test Test1 {\n//   functions [GetOrderInfo]\n//   args {\n//     email {\n//       from_address \"hello@amazon.com\"\n//       subject \"Your Amazon.com order of 'Wood Dowel Rods...' has shipped!\"\n//       body #\"\n//         Hi Sam, your package will arrive:\n//         Thurs, April 4\n//         Track your package:\n//         www.amazon.com/gp/your-account/ship-track?ie=23&orderId123\n\n//         On the way:\n//         Wood Dowel Rods...\n//         Order #113-7540940\n//         Ship to:\n//             Sam\n//             SEATTLE, WA\n\n//         Shipment total:\n//         $0.00\n//     \"#\n\n//     }\n//   }\n// }\n",
}

def get_baml_files():
    return file_map