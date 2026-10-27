from datetime import date
import requests

MAX_GUESSES = 6
WORD_LENGTH = 5
WORDLE_START = date(2021, 6, 19)

def ask_for_date():
    """
    Requests date from user to allow to play today's Wordle or previous ones.

    Returns:
        chosen: date selected in isoformat or None for invalid case
    """
    text = input("Date to play (YYYY-MM-DD), or Enter for today: ").strip()
    if text == "":
        return date.today()
    try:
        chosen = date.fromisoformat(text)
    except ValueError:
        print("Use the format YYYY-MM-DD.")
        return None
    if chosen > date.today():
        print("You can't play a puzzle from the future.")
        return None
    if chosen < WORDLE_START:
        print("Wordle started on 2021-06-19. Pick a later date.")
        return None
    return chosen

def show_wordle_stats(conn, user_id):
    """
    Displays user's Wordle statistics upon request like NYT shows.
    """
    cursor = conn.cursor()

    # Solved games
    cursor.execute(
        "SELECT num_guesses, COUNT(*) FROM wordle_games "
        "WHERE user_id = %s AND solved = 1 GROUP BY num_guesses",
        (user_id,),
    )
    solved_counts = dict(cursor.fetchall())

    # Used all guesses
    cursor.execute(
        "SELECT COUNT(*) FROM wordle_games "
        "WHERE user_id = %s AND solved = 0 AND num_guesses >= %s",
        (user_id, MAX_GUESSES),
    )
    (failed,) = cursor.fetchone()
    cursor.close()

    total_solved = sum(solved_counts.values())
    print(f"\nWordle: solved {total_solved}, failed {failed}")
    if total_solved + failed == 0:
        print("No finished games yet.")
        return

    print("Wordle guess distribution:")
    most = max(solved_counts.values(), default=1)
    for n in range(1, MAX_GUESSES + 1):
        count = solved_counts.get(n, 0)
        bar = "#" * max(1, round(count / most * 20)) if count else ""
        print(f"  {n}: {bar} {count}")

def todays_word(today):
    """
    Requests word from Wordle based on specified `today` date.

    Returns:
        lowercase string representing Wordle solved word
    """
    url = f"https://www.nytimes.com/svc/wordle/v2/{today.isoformat()}.json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["solution"].lower()
    except (requests.RequestException, KeyError, ValueError):
        return None

def score_guess(guess, answer):
    """
    Returns:
        5 character string to score guess:
            '*' = right letter, right spot
            "+' = right letter, wrong spot
            '.' = letter not in the word or already used
    """

    result = ["."] * WORD_LENGTH
    remaining = list(answer)

    # Place GREEN/exact matches
    for i in range(WORD_LENGTH):
        if guess[i] == answer[i]:
            result[i] = "*"
            remaining[i] = None                             # Marked as used

    # Place YELLOW/misplaced matches
    for i in range(WORD_LENGTH):
        if result[i] == "." and guess[i] in remaining:
            result[i] = "+"
            remaining[remaining.index(guess[i])] = None     # Marked as used

    return "".join(result)

def show_guess(guess, feedback):
    """
    Displays user's guess with scored feedback underneath.
    """
    print("  " + "  ".join(guess))
    print("  " + "  ".join(feedback))

def play_wordle(conn, username, today=None):
    """
    Plays Wordle!

    Starts a game or continues an initialized game for specified user. End game
    conditions are correct guess within 6 chances or max guesses used.
    """

    today = today or date.today()
    answer = todays_word(today)
    cursor = conn.cursor()

    # Start new game for today
    cursor.execute(
        "SELECT user_id FROM user_info WHERE username = %s", (username,)
    )
    (user_id,) = cursor.fetchone()

    cursor.execute(
        "SELECT game_id, num_guesses, solved FROM wordle_games "
        "WHERE user_id = %s AND play_date = %s",
        (user_id, today),
    )

    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO wordle_games (user_id, play_date) VALUES (%s, %s)",
            (user_id, today)
        )
        conn.commit()
        game_id, num_guesses, solved = cursor.lastrowid, 0, 0
    else:
        game_id, num_guesses, solved = row

    # Load guesses already made today
    cursor.execute(
        "SELECT guess_word FROM wordle_guesses "
        "WHERE game_id = %s ORDER BY guess_num",
        (game_id,),
    )
    previous = [r[0] for r in cursor.fetchall()]

    print(f"\n=== Wordle for {today} ===")
    print(f"* = correct spot    + = wrong spot  . = not in word\n")
    for g in previous:
        show_guess(g, score_guess(g, answer))

    # Completed already
    if solved:
        print(f"\nYou already solved today's Wordle in {num_guesses}/{MAX_GUESSES}.")
        cursor.close()
        return

    if num_guesses >= MAX_GUESSES:
        print(f"\nYou've used all your guesses today. The word was {answer}.")
        cursor.close()
        return

    while num_guesses < MAX_GUESSES:
        guess = input(
            f"\nGuess {num_guesses + 1}/{MAX_GUESSES} "
            f"(or 'q' to stop and resume later): "
        ).strip().lower()

        if guess == "q":
            print("Progress saved. You can finish today's Wordle later.")
            break
        if len(guess) != WORD_LENGTH or not guess.isascii() or not guess.isalpha():
            print(f"Enter a {WORD_LENGTH}-length word.")
            continue
        if guess in previous:
            print("You already tried that word.")
            continue

        num_guesses += 1
        solved = guess == answer

        # Save guess and updated game state
        cursor.execute(
            "INSERT INTO wordle_guesses (game_id, guess_num, guess_word) "
            "VALUES (%s, %s, %s)",
            (game_id, num_guesses, guess),
        )
        cursor.execute(
            "UPDATE wordle_games SET num_guesses = %s, solved = %s "
            "WHERE game_id = %s",
            (num_guesses, int(solved), game_id),
        )
        conn.commit()

        previous.append(guess)
        show_guess(guess, score_guess(guess, answer))

        if solved:
            print(f"\nYou got it in {num_guesses}/{MAX_GUESSES}")
            break
    else:
        print(f"\nOut of guesses! The word was {answer}.")

    cursor.close()
    