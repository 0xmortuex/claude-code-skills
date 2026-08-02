# atomic-io — example

**Trigger:**

> our worker's `state.json` came back empty this morning — the box got
> OOM-killed overnight and now the process won't boot, `json.load` blows up
> on startup. here's the save function:
>
> ```python
> def save_state(state, path="state.json"):
>     with open(path, "w") as f:
>         json.dump(state, f)
> ```

**Response shape:**

Claude names the exact window the crash landed in, not just "not atomic":

```
`open(path, "w")` truncates state.json to zero bytes the instant it's
called — before json.dump writes a single byte. The OOM-kill landed in
that window: the file was already empty, and dump never got to run, so
what's on disk now is the truncation with nothing after it. This isn't
a corrupted write, it's a write that never happened landing on top of a
destroyed previous version — the old good state is gone too.

  fix: write to state.json.tmp in the same directory, flush + fsync it,
  then os.replace(tmp, path). A reader then only ever sees fully-old or
  fully-new, never the gap in between.
```

It gives the complete four-piece fix, not just "use a temp file":

```python
def save_state(state, path="state.json"):
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)   # atomic on POSIX and Windows
```

Then it checks the read side, since the atomic write alone doesn't fix the
file that's already on disk this morning:

```
This fixes future saves, but doesn't recover from tonight — and it doesn't
protect against a save that completes atomically with bad data. Add
validate-on-read: parse-and-check on load, with a defined fallback instead
of letting JSONDecodeError propagate up through startup.

  on load failure: fall back to state.json.bak if present, else start
  from a known-safe default and log loudly — don't let a bad state file
  block the process from booting at all.
```

It also flags the boundary rather than assuming: is this process the only
writer? If a second worker could call `save_state` concurrently, the atomic
rename alone isn't enough — the second rename silently wins and drops the
first writer's update, which needs a single-writer lock on top, not instead.
