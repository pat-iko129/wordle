# Login System + Wordle

A command-line login system where **hashing and authentication happen
inside MySQL**, not in Python — the same pattern as the CS121-style
project this is based on, cleaned up to fix a SQL-injection issue and
use parameterized queries throughout.

## Login logic

1. **Passwords are never stored in plain text.** `sp_add_user()` generates
   an 8-character random salt (`make_salt()`), hashes `password + salt`
   with SHA-256, and stores only the salt and hash.
2. **Authentication happens in SQL, not Python.** The `authenticate(username,
   password)` SQL function re-hashes the entered password with the user's
   stored salt and compares it to the stored hash — returning `1` or `0`.
   Python just calls `SELECT authenticate(%s, %s)` and reads the result.
3. **Roles come from an `is_admin` flag** on `user_info`. After a
   successful login, the app checks this flag to decide which menu to show.
4. **Two separate MySQL accounts add a second layer of enforcement.**
   Every login initially connects as the low-privilege `appuser` DB account.
   Only after `is_admin` is confirmed does the app reconnect as `appadmin`,
   which has broader privileges. So even a bug in the Python menu code
   can't let a regular user run admin-level queries — the database
   connection itself won't allow it.
5. **All queries use `%s` placeholders**, not string formatting — usernames
   and passwords can never break out of a query and inject arbitrary SQL.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create the database and table:
   ```
   mysql -u root -p < setup.sql
   ```
   or
   ```
   Get-Content setup.sql | mysql -u root -p
   ```

3. Load the password-hashing routines and seed a few example users:
   ```
   mysql -u root -p wordledb < setup-passwords.sql
   ```
   or
   ```
   mysql -u root -p -D wordledb -e "source .\setup-passwords.sql"
   ```

4. Create the two restricted MySQL accounts the app connects as:
   ```
   mysql -u root -p < grant-permissions.sql
   ```
   or
   ```
   Get-Content grant-permissions.sql | mysql -u root -p
   ```

5. Create table for daily Wordle game progress.
   ```
   mysql -u root -p wordledb < wordle.sql
   ```
   or
   ```
   Get-Content wordle.sql | mysql -u root -p
   ```

5. Run the app:
   ```
   python app.py
   ```

## Example accounts (from setup-passwords.sql)

| username    | password    | admin |
|-------------|-------------|-------|
| alice       | alicepass1  | no    |
| pat         | patpass129  | no    |
| bob         | bobpass123  | no    |
| root_admin  | adminpass1  | yes   |

Change or remove these before using this for anything beyond local testing.

## To improve

Note:
- No account lockout persistence (failed-attempt counting resets each run)
- No password reset flow
- No encryption in transit (add `ssl_disabled=False` / proper TLS config
  for a real deployment)
