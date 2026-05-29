package notes

data class Note(val id: String, val title: String, val tags: List<String>)

data class Session(val token: String)

data class NotesQuery(
    val search: String? = null,
    val tag: String? = null,
    val page: Int = 1,
    val pageSize: Int = 20,
)

data class NotesPage(
    val notes: List<Note>,
    val page: Int,
    val totalPages: Int,
    val totalCount: Int,
)

sealed class NotesError : Exception() {
    object Unauthenticated : NotesError()
    data class Server(val msg: String) : NotesError()
}
