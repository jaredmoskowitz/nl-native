# Interaction Spec

## States
- signedOut: no session; any list action yields an unauthenticated error.
- loading: a request is in flight; isLoading is true.
- loaded: notes present; canLoadMore = (page < totalPages).
- error: a user-visible message is set; isLoading is false.

## Transitions
- search and tag-filter always reset to page 1 before loading.
- loadNextPage is a no-op when canLoadMore is false (no request issued).
- a failed first-page load leaves the list empty and sets error.
