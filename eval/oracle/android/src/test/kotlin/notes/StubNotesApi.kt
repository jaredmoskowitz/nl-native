package notes

import kotlin.math.ceil

/** In-memory NotesApi for the oracle: deterministic search/tag/pagination so the
 *  view-model behaviour is the only thing under test. */
class StubNotesApi(
    private val all: List<Note>,
    private val validCredentials: Pair<String, String>? = "a@b.com" to "pw",
    private val failListWith: NotesError? = null,
) : NotesApi {
    var listCallCount = 0
        private set

    override suspend fun login(email: String, password: String): Session {
        val creds = validCredentials
        if (creds != null && creds.first == email && creds.second == password) {
            return Session("tok")
        }
        throw NotesError.Server("Invalid credentials")
    }

    override suspend fun listNotes(query: NotesQuery): NotesPage {
        listCallCount++
        failListWith?.let { throw it }

        var filtered = all
        query.search?.takeIf { it.isNotEmpty() }?.let { s ->
            filtered = filtered.filter { it.title.contains(s, ignoreCase = true) }
        }
        query.tag?.let { t -> filtered = filtered.filter { it.tags.contains(t) } }

        val total = filtered.size
        val size = maxOf(1, query.pageSize)
        val totalPages = maxOf(1, ceil(total.toDouble() / size).toInt())
        val start = (query.page - 1) * size
        val slice = filtered.drop(maxOf(0, start)).take(size)
        return NotesPage(slice, query.page, totalPages, total)
    }
}
