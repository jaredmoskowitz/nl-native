import XCTest
import NotesFeature

@MainActor
final class NotesViewModelOracleTests: XCTestCase {

    private func fixtureNotes() -> [Note] {
        [
            Note(id: "1", title: "Groceries",      tags: ["home"]),
            Note(id: "2", title: "Gym plan",        tags: ["health"]),
            Note(id: "3", title: "Grocery list 2",  tags: ["home"]),
            Note(id: "4", title: "Work tasks",      tags: ["work"]),
            Note(id: "5", title: "Reading",         tags: ["home"]),
        ]
    }

    private func makeVM(_ api: StubNotesAPI) -> NotesViewModel {
        NotesViewModel(api: api, pageSize: 2)
    }

    private func signedIn(_ api: StubNotesAPI) async -> NotesViewModel {
        let vm = makeVM(api)
        await vm.login(email: "a@b.com", password: "pw")
        return vm
    }

    func test_login_success_setsSession() async {
        let vm = makeVM(StubNotesAPI(all: fixtureNotes()))
        await vm.login(email: "a@b.com", password: "pw")
        XCTAssertNotNil(vm.session)
        XCTAssertNil(vm.error)
        XCTAssertFalse(vm.isLoading)
    }

    func test_login_failure_setsErrorNoSession() async {
        let vm = makeVM(StubNotesAPI(all: fixtureNotes()))
        await vm.login(email: "a@b.com", password: "wrong")
        XCTAssertNil(vm.session)
        XCTAssertNotNil(vm.error)
    }

    func test_loadBeforeLogin_setsErrorAndEmptyList() async {
        let vm = makeVM(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        XCTAssertNotNil(vm.error)
        XCTAssertTrue(vm.notes.isEmpty)
        XCTAssertFalse(vm.isLoading)
    }

    func test_refresh_loadsFirstPage() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        XCTAssertEqual(vm.notes.map(\.id), ["1", "2"])
        XCTAssertEqual(vm.page, 1)
        XCTAssertTrue(vm.canLoadMore)
    }

    func test_loadNextPage_appendsAndAdvances() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        await vm.loadNextPage()
        XCTAssertEqual(vm.notes.map(\.id), ["1", "2", "3", "4"])
        XCTAssertEqual(vm.page, 2)
    }

    func test_loadNextPage_stopsAtLastPage() async {
        let api = StubNotesAPI(all: fixtureNotes())
        let vm = await signedIn(api)
        await vm.refresh()       // page 1
        await vm.loadNextPage()  // page 2
        await vm.loadNextPage()  // page 3 (last: 5 notes / 2 => 3 pages)
        XCTAssertEqual(vm.notes.count, 5)
        XCTAssertFalse(vm.canLoadMore)
        let callsBefore = api.listCallCount
        await vm.loadNextPage()  // must be a no-op
        XCTAssertEqual(api.listCallCount, callsBefore,
                       "loadNextPage past the last page must not call the API")
        XCTAssertEqual(vm.notes.count, 5)
    }

    func test_search_resetsToFirstPage() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()
        await vm.loadNextPage()       // now on page 2
        await vm.search("Groc")       // matches "Groceries" + "Grocery list 2"
        XCTAssertEqual(vm.page, 1)
        XCTAssertEqual(vm.notes.map(\.id), ["1", "3"])
        XCTAssertFalse(vm.canLoadMore)
    }

    func test_filterByTag_resetsAndFilters() async {
        let vm = await signedIn(StubNotesAPI(all: fixtureNotes()))
        await vm.refresh()       // page 1
        await vm.loadNextPage()  // advance to page 2 — makes the page-reset assertion load-bearing
        await vm.filterByTag("home")  // ids 1,3,5; page size 2 => page 1 = [1,3]
        XCTAssertEqual(vm.page, 1)
        XCTAssertEqual(vm.notes.map(\.id), ["1", "3"])
        XCTAssertTrue(vm.canLoadMore)
    }

    func test_listError_setsErrorAndClearsLoading() async {
        let api = StubNotesAPI(all: fixtureNotes(), failListWith: .server("boom"))
        let vm = await signedIn(api)
        await vm.refresh()
        XCTAssertEqual(vm.error, "boom")
        XCTAssertFalse(vm.isLoading)
        XCTAssertTrue(vm.notes.isEmpty)
    }
}
