package notes

class NotesViewModel(
    private val api: NotesApi,
    private val pageSize: Int = 20,
) {
    var notes: List<Note> = emptyList()
        private set
    var isLoading: Boolean = false
        private set
    var error: String? = null
        private set
    var page: Int = 1
        private set
    var totalPages: Int = 1
        private set
    var session: Session? = null
        private set

    private var searchText: String? = null
    private var tagFilter: String? = null

    val canLoadMore: Boolean get() = page < totalPages

    suspend fun login(email: String, password: String) {
        isLoading = true
        error = null
        try {
            session = api.login(email, password)
        } catch (e: Throwable) {
            session = null
            error = message(e)
        } finally {
            isLoading = false
        }
    }

    // DEFECT 1: does not reset to page 1 — reloads the current page.
    suspend fun search(text: String) {
        searchText = text.ifEmpty { null }
        load(page, append = false)
    }

    // DEFECT 3: does not reset to page 1 — reloads the current page.
    suspend fun filterByTag(tag: String?) {
        tagFilter = tag
        load(page, append = false)
    }

    suspend fun refresh() {
        load(1, append = false)
    }

    // DEFECT 2: no canLoadMore guard — always requests the next page.
    suspend fun loadNextPage() {
        load(page + 1, append = true)
    }

    private suspend fun load(targetPage: Int, append: Boolean) {
        if (session == null) {
            error = message(NotesError.Unauthenticated)
            return
        }
        isLoading = true
        error = null
        try {
            val result = api.listNotes(NotesQuery(searchText, tagFilter, targetPage, pageSize))
            page = result.page
            totalPages = result.totalPages
            notes = if (append) notes + result.notes else result.notes
        } catch (e: Throwable) {
            error = message(e)
        } finally {
            isLoading = false
        }
    }

    private fun message(e: Throwable): String = when (e) {
        is NotesError.Unauthenticated -> "Not signed in."
        is NotesError.Server -> e.msg
        else -> "Something went wrong."
    }
}
