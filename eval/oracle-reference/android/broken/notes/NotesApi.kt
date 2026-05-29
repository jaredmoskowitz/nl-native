package notes

interface NotesApi {
    suspend fun login(email: String, password: String): Session
    suspend fun listNotes(query: NotesQuery): NotesPage
}
