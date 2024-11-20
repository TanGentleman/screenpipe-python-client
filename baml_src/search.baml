class TimeRange {
  from_time string @description("ISO timestamp to filter results after this time")
  to_time string @description("ISO timestamp to filter results before this time")
}

class SearchParameters {
  content_type "OCR" | "AUDIO" | "ALL" @description("Type of content to search for, defaults to ALL")
  time_range TimeRange? @description("Time range to filter results")
  limit int? @description("Maximum number of results to return")
  search_substring string? @description("Optional substring to filter text content")
  application string? @description("Optional filter to only show results from this application")
}

// class SearchParameters {
//   content_type "OCR" | "AUDIO" | "ALL" @description("Type of content to search for, defaults to ALL")
//   from_time string? @description("ISO timestamp to filter results after this time")
//   to_time string? @description("ISO timestamp to filter results before this time")
//   limit int? @description("Maximum number of results to return")
//   search_substring string? @description("Optional substring to filter text content")
//   application string? @description("Optional filter to only show results from this application")
// }

// Function to construct search parameters from a natural language query
function ConstructSearch(query: string, current_iso_timestamp: string) -> SearchParameters {
  client OllamaQwen
  prompt #"
    Let's construct a search request step by step:
    1) What type of content is being requested (OCR, AUDIO, ALL)?
    2) Is there a specific time range mentioned? If recent/today/etc, use last 2 days. Otherwise, leave null.
    3) Should we limit the number of results?
    4) Has the user asked to filter for a specific word?
    5) Is a specific application mentioned?

    Based on the query: "{{ query }}"
    Current time: {{ current_iso_timestamp }}

    {{ ctx.output_format }}
  "#
}

// Test the search construction
test basic_search {
  functions [ConstructSearch]
  args {
    query #"
      I want to search for all audio content from the last 2 days.
    "#
    current_iso_timestamp #"2024-11-19T12:00:00Z"#
  }
}

test search_with_substring {
  functions [ConstructSearch]
  args {
    query #"
      Find OCR content containing the word 'invoice' from the last week
    "#
    current_iso_timestamp #"2024-11-19T15:30:00Z"#
  }
}

test search_with_application {
  functions [ConstructSearch]
  args {
    query #"
      Analyze my activity this month from the app Discord
    "#
    current_iso_timestamp #"2024-11-19T15:30:00Z"#
  }
}


test search_with_limit {
  functions [ConstructSearch]
  args {
    query #"
      Get the last 5 audio recordings
    "#
    current_iso_timestamp #"2024-11-19T15:30:00Z"#
  }
}

test complex_search {
  functions [ConstructSearch]
  args {
    query #"
      Analyze my screen activity from yesterday using the last 30 OCR results from the app Cursor
    "#
    current_iso_timestamp #"2024-11-19T15:30:00Z"#
  }
}

// NOTE, below from: https://github.com/BoundaryML/baml/blob/canary/fern/01-guide/06-prompt-engineering/chain-of-thought.mdx
// Example
// class Email {
//     subject string
//     body string
//     from_address string
// }


// class OrderInfo {
//     order_status "ORDERED" | "SHIPPED" | "DELIVERED" | "CANCELLED"
//     tracking_number string?
//     estimated_arrival_date string?
// }

// function GetOrderInfo(email: Email) -> OrderInfo {
//   client OllamaQwen
//   prompt #"
//     Extract the info from this email in the INPUT:

//     INPUT:
//     -------
//     from: {{email.from_address}}
//     Email Subject: {{email.subject}}
//     Email Body: {{email.body}}
//     -------

//     {{ ctx.output_format }}

//     Before you output the JSON, please explain your
//     reasoning step-by-step. Here is an example on how to do this:
//     'If we think step by step we can see that ...
//      therefore the output JSON is:
//     {
//       ... the json schema ...
//     }'
//   "#
// }

// test Test1 {
//   functions [GetOrderInfo]
//   args {
//     email {
//       from_address "hello@amazon.com"
//       subject "Your Amazon.com order of 'Wood Dowel Rods...' has shipped!"
//       body #"
//         Hi Sam, your package will arrive:
//         Thurs, April 4
//         Track your package:
//         www.amazon.com/gp/your-account/ship-track?ie=23&orderId123

//         On the way:
//         Wood Dowel Rods...
//         Order #113-7540940
//         Ship to:
//             Sam
//             SEATTLE, WA

//         Shipment total:
//         $0.00
//     "#

//     }
//   }
// }
