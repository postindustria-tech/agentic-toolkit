# Approved reservation rules

## Cancellation

Before cancellation the active status is Reserved, never Pending. Cancellation archives chat read-only for original members. Outsiders cannot read it. This decision controls DEMO-1.

## Confirmation

DEMO-8 must offer Confirm/Keep before cancellation. Keep and Escape preserve data; Confirm cancels once. Initial keyboard focus is Keep.

## Search

Staff reservation searches with no matching records return HTTP 200 and an empty array. Existing matches are unchanged.

## Search UI

An empty array renders No reservations; nonempty arrays render reservation rows.
