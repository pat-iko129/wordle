"""
Login system for Wordle
"""
import sys
from getpass import getpass
import mysql.connector
import mysql.connector.errorcode as errorcode
from wordle import play_wordle, ask_for_date, show_wordle_stats

# Debugging flag to print errors when debugging that shouldn't be visible
# to an actual client. Set to False when done testing.
DEBUG = False
MAX_LOGIN_ATTEMPTS = 5

def get_conn(db_user, db_password):
    """
    Returns a connected MySQL connector instance, if connection is successful.
    If unsuccessful, exits.
    """
    try:
        return mysql.connector.connect(
            host="localhost",
            port="3306",
            user=db_user,
            password=db_password,
            database="wordledb",
        )
    except mysql.connector.Error as err:
        # Remember that this is specific to _database_ users, not
        # application users. So is probably irrelevant to a client in your
        # simulated program. Their user information would be in a users table
        # specific to your database.
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR and DEBUG:
            sys.stderr('Incorrect username or password when connecting to DB.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR and DEBUG:
            sys.stderr('Database does not exist.')
        elif DEBUG:
            sys.stderr(f"Database connection error: {err}")
        else:
            sys.stderr('An error occurred, please contact the administrator.')
        sys.exit(1)

def authenticate(conn, username, password):
    """
    Calls the authenticate SQL function and checks if admin.

    Returns:
        is_valid: boolean of whether salted hash of entered password matches stored hash
        is_admin: boolean of whether user's admin flag is set
    """
    cursor = conn.cursor()
    cursor.execute("SELECT authenticate(%s, %s)", (username, password))
    (result,) = cursor.fetchone()
    is_valid = bool(result)

    is_admin = False
    if is_valid:
        cursor.execute(
            "SELECT is_admin FROM user_info WHERE username = %s", (username,)
        )
        row = cursor.fetchone()
        if row:
            is_admin = bool(row[0])

    cursor.close()
    return is_valid, is_admin


def login():
    """
    Prompts for username/password up to MAX_LOGIN_ATTEMPTS times.
    Returns:
        username, is_admin, conn on success or exits on failure.
    """
    # Connect using a low-privilege account aka user.
    conn = get_conn("appuser", "userpw")

    attempts_left = MAX_LOGIN_ATTEMPTS
    while attempts_left > 0:
        username = input("Username: ").strip()
        password = getpass("Password: ")

        is_valid, is_admin = authenticate(conn, username, password)

        if is_valid:
            print(f"\nLogin successful. Welcome, {username}!")
            if is_admin:
                # Reconnect with the higher-privilege DB account now that
                # we've confirmed this is a real admin.
                conn.close()
                conn = get_conn("appadmin", "adminpw")
            return username, is_admin, conn

        attempts_left -= 1
        # Same message whether the username doesn't exist or the password
        # is wrong, so we don't leak which usernames are registered.
        print(f"Invalid username or password. {attempts_left} attempt(s) left.\n")

    print("Too many failed attempts. Exiting.")
    conn.close()
    sys.exit(1)


def register(conn):
    """
    Creates a new, non-admin account.
    """
    username = input("Choose a username: ").strip()
    password = getpass("Choose a password: ")
    confirm = getpass("Confirm password: ")

    if password != confirm:
        print("Passwords don't match.\n")
        return
    if len(password) < 8:
        print("Password must be at least 8 characters.\n")
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "CALL sp_add_user(%s, %s, %s)", (username, 0, password)
        )
        conn.commit()
        print(f"Account '{username}' created. You can now log in.\n")
    except mysql.connector.IntegrityError:
        print("That username is already taken.\n")
    finally:
        cursor.close()

def user_menu(username, conn):
    """
    Displays user's options and runs them. User can only play Wordle. 
    """
    while True:
        print("\n--- User Menu ---")
        print("(v) view my profile")
        print("(w) play the wordle")
        print("(q) quit\n")
        choice = input("Choose an option: ").strip().lower()

        if choice == "v":
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username, is_admin FROM user_info WHERE username = %s",
                (username,),
            )
            row = cursor.fetchone()
            cursor.close()
            print(f"\nID: {row[0]}  Username: {row[1]}  Admin: {bool(row[2])}")
            show_wordle_stats(conn, row[0])
        elif choice == "w":
            day = ask_for_date()
            if day:
                play_wordle(conn, username, day)
        elif choice == "q":
            break
        else:
            print("Unknown option.")


def admin_menu(username, conn):
    """
    Displays admin's options and runs them. Admin's role is upkeep of db.
    """
    while True:
        print("\n--- Admin Menu ---")
        print("(l) list all users")
        print("(d) delete a user by username")
        print("(q) quit\n")
        choice = input("Choose an option: ").strip().lower()

        if choice == "l":
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, is_admin FROM user_info")
            rows = cursor.fetchall()
            cursor.close()
            print("\nID | Username | Admin")
            for uid, uname, is_adm in rows:
                print(f"{uid:<4}| {uname:<10}| {bool(is_adm)}")
        elif choice == "d":
            target = input("Username to delete: ").strip()
            if target == username:
                print("You can't delete your own account this way.\n")
                continue
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_info WHERE username = %s", (target,))
            conn.commit()
            print(f"Deleted {cursor.rowcount} row(s).\n")
            cursor.close()
        elif choice == "q":
            break
        else:
            print("Unknown option.")

def main():
    print("=== Wordle ===")
    while True:
        print("\n(l) log in")
        print("(r) register")
        print("(q) quit\n")
        choice = input("Choose an option: ").strip().lower()

        if choice == "l":
            username, is_admin, conn = login()
            if is_admin:
                admin_menu(username, conn)
            else:
                user_menu(username, conn)
            conn.close()
        elif choice == "r":
            conn = get_conn("appuser", "userpw")
            register(conn)
            conn.close()
        elif choice == "q":
            print("Goodbye!\n")
            break
        else:
            print("Unknown option.")


if __name__ == "__main__":
    main()
