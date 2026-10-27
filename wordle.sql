-- Tables for the daily Wordle game.

USE wordledb;

-- One row per user per day. UNIQUE key for one Wordle per day.
CREATE TABLE IF NOT EXISTS wordle_games (
    game_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    play_date    DATE NOT NULL,
    num_guesses  TINYINT NOT NULL DEFAULT 0,
    solved       TINYINT NOT NULL DEFAULT 0,   -- 1 = guessed the word
    UNIQUE (user_id, play_date),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
);

-- One row per guess, so a game can be resumed and replayed.
CREATE TABLE IF NOT EXISTS wordle_guesses (
    guess_id     INT AUTO_INCREMENT PRIMARY KEY,
    game_id      INT NOT NULL,
    guess_num    TINYINT NOT NULL,             -- 1 through 6
    guess_word   CHAR(5) NOT NULL,
    UNIQUE (game_id, guess_num),
    FOREIGN KEY (game_id) REFERENCES wordle_games(game_id) ON DELETE CASCADE
);

-- Adjust for Wordle to record games and guesses.
GRANT INSERT, UPDATE ON wordledb.wordle_games   TO 'appuser'@'localhost';
GRANT INSERT         ON wordledb.wordle_guesses TO 'appuser'@'localhost';
FLUSH PRIVILEGES;