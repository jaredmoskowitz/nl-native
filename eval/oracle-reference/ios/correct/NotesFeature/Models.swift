import Foundation

public struct Note: Equatable, Sendable {
    public let id: String
    public let title: String
    public let tags: [String]
    public init(id: String, title: String, tags: [String]) {
        self.id = id
        self.title = title
        self.tags = tags
    }
}

public struct Session: Equatable, Sendable {
    public let token: String
    public init(token: String) { self.token = token }
}

public struct NotesQuery: Equatable, Sendable {
    public var search: String?
    public var tag: String?
    public var page: Int
    public var pageSize: Int
    public init(search: String? = nil, tag: String? = nil, page: Int = 1, pageSize: Int = 20) {
        self.search = search
        self.tag = tag
        self.page = page
        self.pageSize = pageSize
    }
}

public struct NotesPage: Equatable, Sendable {
    public let notes: [Note]
    public let page: Int
    public let totalPages: Int
    public let totalCount: Int
    public init(notes: [Note], page: Int, totalPages: Int, totalCount: Int) {
        self.notes = notes
        self.page = page
        self.totalPages = totalPages
        self.totalCount = totalCount
    }
}

public enum NotesError: Error, Equatable, Sendable {
    case unauthenticated
    case server(String)
}
