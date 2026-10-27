# Login System + Wordle
A command-line login system with hashing and authentication inside MYSQL.

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
