public protocol NotesAPI: Sendable {
    func login(email: String, password: String) async throws -> Session
    func listNotes(_ query: NotesQuery) async throws -> NotesPage
}
