import Foundation
import NotesFeature

/// In-memory NotesAPI used by the oracle. Applies search, tag, and pagination
/// deterministically so view-model behaviour is the only thing under test.
final class StubNotesAPI: NotesAPI, @unchecked Sendable {
    let all: [Note]
    let validCredentials: (email: String, password: String)?
    let failListWith: NotesError?
    private(set) var listCallCount = 0

    init(all: [Note],
         validCredentials: (email: String, password: String)? = ("a@b.com", "pw"),
         failListWith: NotesError? = nil) {
        self.all = all
        self.validCredentials = validCredentials
        self.failListWith = failListWith
    }

    func login(email: String, password: String) async throws -> Session {
        if let c = validCredentials, c.email == email, c.password == password {
            return Session(token: "tok")
        }
        throw NotesError.server("Invalid credentials")
    }

    func listNotes(_ query: NotesQuery) async throws -> NotesPage {
        listCallCount += 1
        if let failure = failListWith { throw failure }

        var filtered = all
        if let s = query.search, !s.isEmpty {
            filtered = filtered.filter { $0.title.range(of: s, options: .caseInsensitive) != nil }
        }
        if let t = query.tag {
            filtered = filtered.filter { $0.tags.contains(t) }
        }

        let total = filtered.count
        let size = max(1, query.pageSize)
        let totalPages = max(1, Int(ceil(Double(total) / Double(size))))
        let start = (query.page - 1) * size
        let slice = Array(filtered.dropFirst(max(0, start)).prefix(size))
        return NotesPage(notes: slice, page: query.page, totalPages: totalPages, totalCount: total)
    }
}
