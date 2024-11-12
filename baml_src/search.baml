// Defining the search parameters data model
class SearchParameters {
  limit int
  content_type string
  search_substring string?
  start_time string?
  end_time string?
  app_name string?
}

// Inject a list of "system" or "user" messages into the prompt.
// template_string PrintMessages(messages: Message[]) #"
//   {% for m in messages %}
//     {{ _.role(m.role) }}
//     {{ m.message }}
//   {% endfor %}
// "#

// function ClassifyConversation(messages: Message[]) -> Category[] {
//   client GPT4Turbo
//   prompt #"
//     Classify this conversation:
//     {{ PrintMessages(messages) }}

//     Use the following categories:
//     {{ ctx.output_format}}
//   "#
// }

// Create a function to validate and process search parameters
function ConstructSearchParameters(query: string, current_iso_timestamp: string) -> SearchParameters {
  client CustomLlama
  prompt #"
    {{ _.role("system") }} 
    Construct search parameters given a query.

    Ensure the following rules are met:
    - limit must be between 1 and 100. defaults to 5 if not specified.
    - content_type must be one of: "ocr", "audio", "all"
    - time values should be null or in ISO format relative to the current timestamp: {{ current_iso_timestamp }}

    {{ ctx.output_format }}

    {{ _.role("user") }}
    QUERY: {{ query }}
    - The current time is {{ current_iso_timestamp }}
  "#
}

// Test the function with sample search parameters
test basic_search {
  functions [ConstructSearchParameters]
  args {
    query #"
      I want to search for all ocr content from the last 24 hours.
    "#
    current_iso_timestamp #"2024-11-12T12:00:00Z"#
  }
} 