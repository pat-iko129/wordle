-- Creates the database and the users table.

DROP DATABASE IF EXISTS wordledb;
CREATE DATABASE wordledb;
USE wordledb;

CREATE TABLE user_info (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(20)  NOT NULL UNIQUE,
    is_admin       TINYINT      NOT NULL DEFAULT 0,  -- 0 = regular user, 1 = admin
    -- Salt is randomly generated per-user for unique passwords. We make it 8 characters
    -- all the time.
    salt           CHAR(8)      NOT NULL,
    -- SHA-2 with 256-bit hash. MySQL retruns hash value as hexadecimal string, which means
    -- each byte is represented as 2 char. Thus, 256 / 8 * 2 = 64.
    -- We can use BINARY or CHAR. BINARY has different defintion for comparison/sorting than CHAR
    password_hash  BINARY(64)   NOT NULL
);
