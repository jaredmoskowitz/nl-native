import Foundation

@MainActor
public final class NotesViewModel {
    public private(set) var notes: [Note] = []
    public private(set) var isLoading = false
    public private(set) var error: String?
    public private(set) var page = 1
    public private(set) var totalPages = 1
    public private(set) var session: Session?

    private let api: NotesAPI
    private let pageSize: Int
    private var searchText: String?
    private var tagFilter: String?

    public init(api: NotesAPI, pageSize: Int = 20) {
        self.api = api
        self.pageSize = pageSize
    }

    public var canLoadMore: Bool { page < totalPages }

    public func login(email: String, password: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            session = try await api.login(email: email, password: password)
        } catch {
            session = nil
            self.error = Self.message(error)
        }
    }

    // DEFECT 1: does not reset to page 1 — reloads the current page.
    public func search(_ text: String) async {
        searchText = text.isEmpty ? nil : text
        await load(targetPage: page, append: false)
    }

    public func filterByTag(_ tag: String?) async {
        tagFilter = tag
        await load(targetPage: 1, append: false)
    }

    public func refresh() async {
        await load(targetPage: 1, append: false)
    }

    // DEFECT 2: no canLoadMore guard — always requests the next page.
    public func loadNextPage() async {
        await load(targetPage: page + 1, append: true)
    }

    private func load(targetPage: Int, append: Bool) async {
        guard session != nil else {
            error = Self.message(NotesError.unauthenticated)
            return
        }
        isLoading = true
        error = nil
        defer { isLoading = false }
        do {
            let query = NotesQuery(search: searchText, tag: tagFilter, page: targetPage, pageSize: pageSize)
            let result = try await api.listNotes(query)
            page = result.page
            totalPages = result.totalPages
            if append {
                notes += result.notes
            } else {
                notes = result.notes
            }
        } catch {
            self.error = Self.message(error)
        }
    }

    private static func message(_ error: Error) -> String {
        if let e = error as? NotesError {
            switch e {
            case .unauthenticated: return "Not signed in."
            case .server(let m):   return m
            }
        }
        return "Something went wrong."
    }
}
