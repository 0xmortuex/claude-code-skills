# push-guard — example

**Trigger:**

> my dad used my old phone after I signed out of the app and gave it to
> him, and now he's getting *my* order-shipped notifications on *his*
> account. did we mess up logout? here's the relevant client and server
> code:
>
> ```js
> // client: notifications.js
> messaging().onTokenRefresh(async (newToken) => {
>   await api.post('/devices/register', { token: newToken });
> });
>
> async function logout() {
>   const token = await AsyncStorage.getItem('pushToken');
>   await api.post('/devices/unregister', { token: 'token' }); // typo, should be `token`
>   await AsyncStorage.clear();
>   navigation.reset({ routes: [{ name: 'Login' }] });
> }
> ```
>
> ```js
> // server: routes/devices.js
> router.post('/devices/register', requireAuth, async (req, res) => {
>   await Device.create({ userId: req.user.id, token: req.body.token });
>   res.json({ ok: true });
> });
>
> router.post('/devices/unregister', requireAuth, async (req, res) => {
>   await Device.deleteMany({ userId: req.user.id, token: req.body.token });
>   res.json({ ok: true });
> });
>
> // send path
> async function sendOrderShipped(userId, order) {
>   const devices = await Device.find({ userId });
>   for (const d of devices) {
>     try {
>       await fcm.send({ token: d.token, notification: {
>         title: 'Order shipped!',
>         body: `Your order #${order.number} ($${order.total}) is on its way`,
>       }});
>     } catch (e) {
>       console.error('push send failed, will retry next run', e);
>     }
>   }
> }
> ```

**Response shape:**

Step 1 traces the logout call site, not just whether a call exists:

```
Step 1: registration and logout
- Registration: onTokenRefresh posts to /devices/register, which creates
  a new Device row scoped to the current user. Fine on its own.
- Logout: reads the real token into `token`, then never uses it — the
  unregister call sends the literal string `'token'` as the value
  instead of the variable. `Device.deleteMany` matches on
  `{ userId, token: 'token' }`, which will never match the row actually
  stored (a real FCM token), so the delete is a silent no-op every time.
  This is the exact `noticeboard-mobile-app`#58 shape: the delete call
  exists, looks correct at a glance, and simply doesn't match anything.
- Account switch: logout clears local storage and navigates to the
  login screen, but since the server-side row was never removed, the
  next person to log in on this physical device inherits a device list
  that still has the previous user's live, unregistered token sitting
  in it under the *previous* user's userId — the row is still correctly
  scoped to the dad's son's account, so the son keeps receiving pushes
  regardless of who's holding the phone now.
```

Step 2 checks token-refresh handling for the separate duplication risk:

```
Step 2: token refresh
onTokenRefresh always calls /devices/register, which always
`Device.create`s a new row — there's no upsert or replace-by-install-id.
Not the reported bug, but a second real gap: every OS-issued refresh for
the same install adds another live row for the same user instead of
replacing the old one, so a long-lived install can accumulate several
tokens, some already stale, all still targeted by every future send.
```

Step 3 checks the send path's handling of a provider-reported dead token:

```
Step 3: dead-token handling
sendOrderShipped's catch block treats every failure identically —
"will retry next run" — with no branch reading the FCM error code. A
404/UNREGISTERED response (Firebase's own documented signal to delete
that registration) is swallowed the same as a transient network error.
Combined with step 2's duplicate-row accumulation, the Device table for
an active user can only grow: nothing in this codebase ever removes a
row, whether because the account it belonged to logged out (step 1) or
because the provider says the token is dead (this step).
```

Step 4 checks what the misrouted notification actually exposed:

```
Step 4: payload exposure
The notification body is not generic — it interpolates the order
number and dollar total directly into `body`. The dad didn't just get
an unwanted ping; he saw his son's specific order total. This is a data
exposure on top of the trust/UX problem, not just an annoyance.
```

Report:

```
## push-guard review: devices.js / notifications.js

1. Logout's unregister call sends a hardcoded `'token'` string instead
   of the variable holding the real token (BLOCK — confirmed root
   cause): `Device.deleteMany` never matches the stored row, so logout
   never actually removes server-side push targeting. Fix: pass the
   variable (`req.body` should carry the actual `token` value read from
   storage — the client bug is `{ token: 'token' }`, not a scoping
   issue on the server).

2. The exposed payload carries real order content (order number, dollar
   total) (BLOCK, same finding as #1 but changes severity): a lifecycle
   bug that would otherwise be an annoying misdirected ping is instead
   handing one user's order details to whoever holds the device next.

3. Token refresh always inserts a new row instead of replacing the
   install's existing one (CAUTION): not the reported bug, but the same
   root shape — nothing here ever retires a token — and it will keep
   producing duplicate/stale rows even after finding 1 is fixed.

4. The send path has no handling for a provider-reported dead token —
   every failure hits the same "retry next run" branch (CAUTION): once
   findings 1 and 3 are fixed this stops making the problem worse, but
   it's still a real gap that will eventually surface as declining
   delivery rates with no mechanism to diagnose why.

## Verdict: BLOCK
The son's account never actually released this device's push target on
logout, and the payload it kept receiving contained specific order
details — not a generic ping. Fix the unregister call first (it's a
one-line client bug with a clear reproduction), then address the
token-refresh duplication and missing dead-token handling so the same
device-list table doesn't quietly re-accumulate the same class of
problem going forward.
```
