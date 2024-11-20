// Main search class to represent a search request

enum ContentType {
  OCR
  AUDIO
  ALL
}

class TimeRange {
  from_time string @description("ISO timestamp to filter results after this time")
  to_time string @description("ISO timestamp to filter results before this time")
}

// Search parameters for filtering content
// class SearchParameters {
//   content_type ContentType @description("Type of content to search for, defaults to ALL")
//   from_time string? @description("ISO timestamp to filter results after this time")
//   to_time string? @description("ISO timestamp to filter results before this time")
//   limit int? @description("Maximum number of results to return")
//   search_substring string? @description("Optional substring to filter text content")
//   application string? @description("Optional filter to only show results from this application")
// }

class SearchParameters {
  content_type ContentType @description("Type of content to search for, defaults to ALL")
  time_range TimeRange? @description("Time range to filter results")
  limit int? @description("Maximum number of results to return")
  search_substring string? @description("Optional substring to filter text content")
  application string? @description("Optional filter to only show results from this application")
}

// class SearchParameters {
//   content_type string @description("Type of content to search for, defaults to ALL")
//   from_time string? @description("ISO timestamp to filter results after this time")
//   to_time string? @description("ISO timestamp to filter results before this time")
//   limit int? @description("Maximum number of results to return")
//   search_substring string? @description("Optional substring to filter text content")
//   application string? @description("Optional filter to only show results from this application")
// }

// Function to construct search parameters from a natural language query
function ConstructSearch(query: string, current_iso_timestamp: string) -> SearchParameters {
  client GeminiFlash
  prompt #"
    Construct a search request to retrieve content from the database. All fields are optional except for content_type. If the user requests recent results, default to the last 48 hours.
    {{ ctx.output_format }}

    {{ _.role("user") }}
    USER QUERY: {{ query }}
    CURRENT TIME: {{ current_iso_timestamp }}
  "#
}

// Test the search construction
test basic_search {
  functions [ConstructSearch]
  args {
    query #"
      I want to search for all audio content from the last 48 hours.
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
