# clipboard-guard — example

**Trigger:**

> we added a "copy code" button for our login OTP and a way to copy your
> API key from account settings. can you check the clipboard handling
> before we ship?
>
> ```js
> // account settings: copy API key
> function copyApiKey(key) {
>   navigator.clipboard.writeText(key);
>   toast.show('API key copied');
> }
>
> // login: OTP screen
> function copyOtpCode(code) {
>   navigator.clipboard.writeText(code);
> }
>
> // login: auto-detect pasted OTP from clipboard
> useEffect(() => {
>   const interval = setInterval(async () => {
>     const text = await navigator.clipboard.readText();
>     if (/^\d{6}$/.test(text)) {
>       setOtpField(text);
>     }
>   }, 1000);
>   return () => clearInterval(interval);
> }, []);
> ```

**Response shape:**

Step 1 enumerates every clipboard write and read:

```
Step 1: writes and reads
- Write: API key copied via `copyApiKey` — long-lived, high-value secret.
- Write: OTP code copied via `copyOtpCode` — short-lived, high-value secret.
- Read: a `setInterval` polls `navigator.clipboard.readText()` every
  second on the login screen, unconditionally, looking for a 6-digit
  string — this is a read, not gated on any paste action.
```

Step 2 checks whether either write is ever taken back:

```
Step 2: app-side clear and platform flag
- API key: `navigator.clipboard.writeText(key)` — no auto-clear, no
  expiring/sensitive flag (the web Clipboard API has no such flag; this
  question matters more on iOS/Android native clipboards, but the lack of
  any clear at all is the bigger problem here regardless of platform).
  The key sits on the clipboard indefinitely until the user copies
  something else over it.
- OTP: same — `writeText(code)` with no clear at all. A short-lived code
  that should matter for seconds has no expiry and will sit on the
  clipboard long after the login completes.
```

Step 3 checks whether the clipboard read is gated on an explicit paste:

```
Step 3: the read is unconditional
The `setInterval` reads the clipboard every second on a timer, for as
long as the login screen is mounted — not in response to any paste
action the user takes. This is exactly the 2020 iOS-wave shape: reading
"because the screen is open," not "because the user pasted." It will
pick up and auto-fill *any* 6-digit string currently on the clipboard,
including one the user copied from somewhere else entirely for an
unrelated reason, and it does so without the browser's native paste
permission prompt that a real paste event would trigger.
```

Step 4 names the boundary:

```
Step 4: what's already out of reach
Because neither write ever clears, and the web Clipboard API offers no
sensitive/expiring flag to opt out of OS-level persistence, both values
are candidates for whatever clipboard-history feature the OS or browser
provides (Windows Cloud Clipboard, a browser extension's clipboard
manager) for as long as they sit uncleared — there's no code-side fix for
history capture that already happened, only not leaving the value there
to be captured.
```

Report:

```
## clipboard-guard review: settings.js, login.js

1. Neither the API key nor the OTP code is ever cleared from the
   clipboard (BLOCK): both `writeText` calls have no follow-up clear.
   The OTP in particular is meant to be single-use and short-lived; as
   written it persists on the clipboard indefinitely. Fix: clear the
   clipboard a few seconds after copy, or once the value has been pasted
   once (e.g. `navigator.clipboard.writeText('')` on a timeout, accepting
   this needs explicit document-focus handling in browsers that restrict
   clipboard writes to focused tabs).

2. The OTP screen reads the clipboard unconditionally on a 1-second timer
   rather than in response to a paste action (BLOCK): this picks up any
   6-digit string currently on the clipboard regardless of its source,
   and does so continuously for as long as the screen is open. Fix: read
   the clipboard only from an explicit "paste code" button or a real
   paste event, not a polling interval.

3. No clipboard-write ever carries a sensitive/expiring flag (CAUTION,
   platform-dependent): the web Clipboard API has no equivalent of
   `UIPasteboard.expirationDate` or `ClipDescription.EXTRA_IS_SENSITIVE`,
   so this gap is inherent to the web client; if a native iOS/Android
   client reuses this copy logic, set the platform flag there — it isn't
   available here, but shouldn't be skipped where it is.

## Verdict: BLOCK
Two independent high-value secrets (an API key and a login OTP) are
copied to the clipboard with no clear at all, and the OTP screen reads
the clipboard unconditionally on a timer rather than on an explicit
paste — fix both before shipping. The missing platform sensitive-flag is
a lower-priority follow-up specific to any native client, not a blocker
for the web path shown here.
```
