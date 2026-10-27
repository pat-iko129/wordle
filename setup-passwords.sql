-- Password management: salting, hashing, and authentication

USE wordledb;

-- Drop procedures and functions if they already exist so we do not get errors
DROP PROCEDURE IF EXISTS sp_add_user;
DROP FUNCTION IF EXISTS authenticate;
DROP FUNCTION IF EXISTS make_salt;

-- Generates a specified number of characters for 
-- using as a salt in passwords.
DELIMITER !
CREATE FUNCTION make_salt(num_chars INT)
RETURNS VARCHAR(20) DETERMINISTIC
BEGIN
    DECLARE salt VARCHAR(20) DEFAULT '';
    SET num_chars = LEAST(20, num_chars);
    WHILE num_chars > 0 DO
        SET salt = CONCAT(salt, CHAR(32 + FLOOR(RAND() * 95)));
        SET num_chars = num_chars - 1;
    END WHILE;
    RETURN salt;
END !
DELIMITER ;

-- Adds a new user to the user_info table, using the specified password (max
-- of 50 characters). Salts the password with a newly-generated salt value,
-- and then the salt and hash values are both stored in the table.
DELIMITER !
CREATE PROCEDURE sp_add_user(
    IN new_username VARCHAR(20),
    IN admin_flag TINYINT,
    IN plain_password VARCHAR(50)
)
BEGIN
    DECLARE new_salt CHAR(8);
    DECLARE pw_hash BINARY(64);

    SET new_salt = make_salt(8);
    SET pw_hash = SHA2(CONCAT(plain_password, new_salt), 256);

    INSERT INTO user_info (username, is_admin, salt, password_hash)
    VALUES (new_username, admin_flag, new_salt, pw_hash);
END !
DELIMITER ;

-- Authenticates the specified username and password against the data
-- in the user_info table.  Returns 1 if the user appears in the table, and the
-- specified password hashes to the value for the user. Otherwise returns 0.
DELIMITER !
CREATE FUNCTION authenticate(check_username VARCHAR(20), plain_password VARCHAR(50))
RETURNS TINYINT DETERMINISTIC
BEGIN
    DECLARE check_salt CHAR(8);
    DECLARE stored_hash BINARY(64);
    DECLARE attempt_hash BINARY(64);

    SELECT salt, password_hash INTO check_salt, stored_hash
    FROM user_info
    WHERE username = check_username
    LIMIT 1;

    -- If no such user, check_salt is NULL and this will cause a failed match.
    SET attempt_hash = SHA2(CONCAT(plain_password, check_salt), 256);

    IF stored_hash IS NOT NULL AND attempt_hash = stored_hash THEN
        RETURN 1;
    ELSE
        RETURN 0;
    END IF;
END !
DELIMITER ;

-- Example users (change/remove these before real use)
CALL sp_add_user('alice', 0, 'alicepass1');
CALL sp_add_user('bob',   0, 'bobpass123');
CALL sp_add_user('pat', 0, 'patpass129');
CALL sp_add_user('root_admin', 1, 'adminpass1');
