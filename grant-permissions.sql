-- Creates two MySQL database users with different privilege levels

-- Drop the users if they already exist so when the file is sourced from the 
-- command line we will not get errors
DROP USER IF EXISTS 'appadmin'@'localhost';
DROP USER IF EXISTS 'appuser'@'localhost';

-- Create admin and client users
CREATE USER 'appadmin'@'localhost' IDENTIFIED BY 'adminpw';
CREATE USER 'appuser'@'localhost'  IDENTIFIED BY 'userpw';

-- Grant all privileges to the admin
GRANT ALL PRIVILEGES ON wordledb.* TO 'appadmin'@'localhost';

-- Grant only slect and execute privileges to user.
GRANT SELECT, EXECUTE ON wordledb.* TO 'appuser'@'localhost';

FLUSH PRIVILEGES;
