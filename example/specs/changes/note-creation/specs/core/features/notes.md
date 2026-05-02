# Feature: Notes
Version: 1.0.0
Status: approved

## Summary

Users can create personal notes with a title and body, view a list of all their notes in reverse chronological order, and delete notes they no longer need. Notes are stored server-side and persist across sessions and devices.

## Scope

**In scope:** Create, list, delete notes. Server-side persistence. Auth-gated (users see only their own notes).

**Out of scope:** Edit after creation, sharing, rich text, attachments, search.

## Requirements

### Listing notes

- REQ-001: When the notes screen opens, the system shall fetch and display all notes belonging to the authenticated user, ordered by creation time descending.
- REQ-002: While notes are being fetched, the system shall display a loading indicator.
- REQ-003: If the user has no notes, the system shall display an empty state with a prompt to create the first note.
- REQ-004: If the fetch fails, the system shall display an error state with an option to retry.
- REQ-005: The system shall display each note's title and a truncated preview of the body (maximum 2 lines).
- REQ-006: The system shall display each note's creation timestamp in a human-readable relative format (e.g. "2 hours ago").

### Creating a note

- REQ-007: When the user initiates note creation, the system shall present a note editor.
- REQ-008: The system shall require a title to save a note. The body is optional.
- REQ-009: When the user saves a note, the system shall persist it to the server and add it to the top of the notes list.
- REQ-010: If saving fails, the system shall notify the user and allow them to retry without losing their content.
- REQ-011: When the user dismisses the editor without saving, the system shall discard the draft without prompting if the editor is empty. If the editor contains content, the system shall confirm before discarding.

### Deleting a note

- REQ-012: When the user initiates deletion of a note, the system shall ask for confirmation before deleting.
- REQ-013: When the user confirms deletion, the system shall delete the note from the server and remove it from the list.
- REQ-014: If deletion fails, the system shall notify the user and restore the note to the list.
- REQ-015: The system shall not allow bulk deletion in this version.

## Scenarios

### User views their notes

**Given** the user is authenticated and has three notes
**When** the notes screen opens
**Then** all three notes are displayed, newest first
**And** each shows its title, body preview, and relative timestamp

### User views notes for the first time (empty state)

**Given** the user is authenticated and has no notes
**When** the notes screen opens
**Then** an empty state is shown with a prompt to create the first note

### Fetch fails on open

**Given** the device has no network connectivity
**When** the notes screen opens
**Then** a loading indicator appears briefly, then an error state with a Retry button

### User creates a note successfully

**Given** the user is on the notes screen
**When** they initiate creation, enter "Shopping list" as the title and "Milk, eggs, bread" as the body, and save
**Then** the editor closes, the new note appears at the top of the list
**And** the note shows "Shopping list", a preview of the body, and "just now"

### User tries to save a note with no title

**Given** the user is in the note editor
**When** they attempt to save with the title field empty
**Then** the save is blocked and the title field is highlighted as required

### Save fails

**Given** the user has written a note and tapped Save
**When** the server returns an error
**Then** the editor remains open with the user's content intact
**And** an error message is shown with a Retry option

### User deletes a note

**Given** the user is viewing their notes and initiates deletion of "Shopping list"
**When** they confirm the deletion
**Then** "Shopping list" is removed from the list

### User cancels deletion

**Given** the user initiates deletion of a note
**When** they dismiss the confirmation without confirming
**Then** the note remains in the list unchanged

### User dismisses empty editor

**Given** the user opens the editor and types nothing
**When** they dismiss the editor
**Then** it closes without prompting

### User dismisses editor with content

**Given** the user has typed content into the editor
**When** they attempt to dismiss
**Then** a confirmation prompt asks if they want to discard their draft
**And** confirming closes the editor; canceling returns them to editing
