---
name: codebase-tour
description: Orient someone in an unfamiliar codebase — the entry points, the architecture, the request/data flow, and where you'd go to make a given change — by reading the actual code and mapping it, not by summarizing the file tree. Use this whenever the user is new to a repo, asks "how does this work", "where do I start", "walk me through this codebase", "how is this organized", "where would I add X", or has just cloned/inherited a project and needs to get productive. Also use when onboarding to a large or undocumented codebase.
---

# codebase-tour

Dropping into an unfamiliar codebase is disorienting because the file tree tells you what exists but not how it fits together or where to stand. A good tour answers the questions a new contributor actually has, in the order they have them: *What is this? How does a request/action flow through it? Where do I change the thing I came here to change?* You produce that by tracing real code paths, not by narrating directory names.

## How to explore — trace, don't list

Listing folders is the shallow version and it's not useful. Trace execution instead:

1. **Find the true entry point** and start there — `main`, the server bootstrap, the CLI dispatch, the app root. Read it. What does it wire up?
2. **Follow one real path end to end.** Pick the most representative action (an HTTP request, a CLI command, the core job) and follow it through the layers: route → handler → service/domain logic → data access → response. This single trace teaches more than reading ten files in isolation.
3. **Identify the layers and the seams.** Where are the boundaries — routing, business logic, persistence, external calls? How do modules depend on each other? What's the shared vocabulary (the core domain types everything passes around)?
4. **Read the manifest and config** for the dependency list, scripts, and what external services it talks to.
5. **Let the tests show you intended usage** — they're the most honest documentation of how the code is meant to be called.
6. **Note the conventions** a newcomer would trip on: the error-handling pattern, how config/secrets are loaded, the naming scheme, anything non-obvious that "everyone here just knows."

Scale the depth to the codebase and the ask. A focused "where do I add a new API endpoint" needs one precise trace and a pointer; "walk me through this whole system" needs the full map.

## Output: a map that ends at "where do I go"

Write for someone who will *edit* this code within the hour, not someone reading for trivia. Ground every claim in real paths (`src/auth/session.ts:42`) so they can click straight there.

```
## What this is
1-3 sentences: the purpose, the kind of system (web API, CLI, library, worker),
the main language/framework.

## The lay of the land
The handful of directories/modules that matter and what each is responsible
for — not an exhaustive tree, just the ones a contributor needs. `path/` — role.

## How it flows
A concrete trace of one representative path, layer by layer, with file:line
references. This is the heart of the tour — the thing that makes the structure
click. A small diagram if it helps.

## Where you'd make common changes
The payoff. For the kinds of change someone is likely here to make:
- To add/change <X>: start in `path`, because …
- To touch <Y>: `path`.
Point at the exact files, and note anything they'd need to update alongside
(a test, a registration, a migration, a type).

## Things to know before you touch it
Conventions and gotchas: the error pattern, how config is loaded, anything
surprising or fragile. What a newcomer would get wrong on their first PR.
```

## Principles

- **Depth over breadth.** One code path traced properly beats a summary of every folder. The goal is understanding, and understanding comes from following how things actually connect.
- **Always land on "where do I go."** Orientation that doesn't tell someone where to make their change is trivia. The tour is a means to getting productive.
- **Cite real locations.** `file:line` references turn the map into something clickable and verifiable — and prove you read the code rather than guessed from names.
- **Be honest about mess.** If the architecture is inconsistent or a module is a tangle, say so — a newcomer benefits far more from "auth logic is split between `middleware/` and `services/user`, confusingly" than from a tidy fiction.
- **Match the ask.** Tune scope to what they need — a targeted pointer or a full walkthrough — instead of always producing the maximal tour.
