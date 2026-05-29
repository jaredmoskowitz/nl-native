package notes

import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class NotesViewModelOracleTest {

    private fun fixture() = listOf(
        Note("1", "Groceries", listOf("home")),
        Note("2", "Gym plan", listOf("health")),
        Note("3", "Grocery list 2", listOf("home")),
        Note("4", "Work tasks", listOf("work")),
        Note("5", "Reading", listOf("home")),
    )

    private fun vm(api: StubNotesApi) = NotesViewModel(api, pageSize = 2)

    private suspend fun signedIn(api: StubNotesApi): NotesViewModel {
        val v = vm(api)
        v.login("a@b.com", "pw")
        return v
    }

    @Test fun login_success_setsSession() = runTest {
        val v = vm(StubNotesApi(fixture()))
        v.login("a@b.com", "pw")
        assertNotNull(v.session)
        assertNull(v.error)
        assertFalse(v.isLoading)
    }

    @Test fun login_failure_setsErrorNoSession() = runTest {
        val v = vm(StubNotesApi(fixture()))
        v.login("a@b.com", "wrong")
        assertNull(v.session)
        assertNotNull(v.error)
    }

    @Test fun loadBeforeLogin_setsErrorAndEmptyList() = runTest {
        val v = vm(StubNotesApi(fixture()))
        v.refresh()
        assertNotNull(v.error)
        assertTrue(v.notes.isEmpty())
        assertFalse(v.isLoading)
    }

    @Test fun refresh_loadsFirstPage() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        assertEquals(listOf("1", "2"), v.notes.map { it.id })
        assertEquals(1, v.page)
        assertTrue(v.canLoadMore)
    }

    @Test fun loadNextPage_appendsAndAdvances() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        v.loadNextPage()
        assertEquals(listOf("1", "2", "3", "4"), v.notes.map { it.id })
        assertEquals(2, v.page)
    }

    @Test fun loadNextPage_stopsAtLastPage() = runTest {
        val api = StubNotesApi(fixture())
        val v = signedIn(api)
        v.refresh()
        v.loadNextPage()
        v.loadNextPage()
        assertEquals(5, v.notes.size)
        assertFalse(v.canLoadMore)
        val callsBefore = api.listCallCount
        v.loadNextPage()
        assertEquals(callsBefore, api.listCallCount, "loadNextPage past the last page must not call the API")
        assertEquals(5, v.notes.size)
    }

    @Test fun search_resetsToFirstPage() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        v.loadNextPage()
        v.search("Groc")
        assertEquals(1, v.page)
        assertEquals(listOf("1", "3"), v.notes.map { it.id })
        assertFalse(v.canLoadMore)
    }

    @Test fun filterByTag_resetsAndFilters() = runTest {
        val v = signedIn(StubNotesApi(fixture()))
        v.refresh()
        v.loadNextPage()
        v.filterByTag("home")
        assertEquals(1, v.page)
        assertEquals(listOf("1", "3"), v.notes.map { it.id })
        assertTrue(v.canLoadMore)
    }

    @Test fun listError_setsErrorAndClearsLoading() = runTest {
        val api = StubNotesApi(fixture(), failListWith = NotesError.Server("boom"))
        val v = signedIn(api)
        v.refresh()
        assertEquals("boom", v.error)
        assertFalse(v.isLoading)
        assertTrue(v.notes.isEmpty())
    }
}
