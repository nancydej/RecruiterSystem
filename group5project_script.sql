-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE;
SET SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION';

DROP SCHEMA IF EXISTS `group5`;
CREATE SCHEMA IF NOT EXISTS `group5` DEFAULT CHARACTER SET utf8;
USE `group5`;

##########################################################
# Table: users
##########################################################

CREATE TABLE `users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `first_name` VARCHAR(50) NULL,
  `last_name` VARCHAR(50) NULL,
  `email` VARCHAR(100) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `phone_number` VARCHAR(15) NOT NULL,
  `role` ENUM('Admin', 'Event Coordinator', 'Recruiter') NOT NULL,

  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `username_UNIQUE` (`username`),
  UNIQUE INDEX `email_UNIQUE` (`email`),
  INDEX `idx_role` (`role`)
) ENGINE=InnoDB;

##########################################################
# Table: events
##########################################################

CREATE TABLE `events` (
  `event_id` INT NOT NULL AUTO_INCREMENT,
  `created_by` INT NOT NULL,
  `event_name` VARCHAR(100) NOT NULL,
  `description` TEXT,
  `city` VARCHAR(50) NOT NULL,
  `state` VARCHAR(50) NOT NULL,
  `event_datetime` DATETIME NOT NULL,
  `capacity` INT NOT NULL,

  PRIMARY KEY (`event_id`),
  INDEX `idx_created_by` (`created_by`),
  INDEX `idx_event_datetime` (`event_datetime`),

  CONSTRAINT `fk_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,

  CONSTRAINT `chk_capacity`
    CHECK (`capacity` BETWEEN 3 AND 10)
) ENGINE=InnoDB;

##########################################################
# Table: registrations
##########################################################

CREATE TABLE `registrations` (
  `registration_id` INT NOT NULL AUTO_INCREMENT,
  `recruiter_id` INT NOT NULL,
  `event_id` INT NOT NULL,

  `status` ENUM(
    'PENDING',
    'APPROVED',
    'CANCELLED_FULL_REFUND',
    'CANCELLED_PARTIAL_REFUND',
    'CANCELLED_NO_REFUND'
  ) NOT NULL DEFAULT 'PENDING',

  `registration_datetime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cancel_datetime` DATETIME NULL,
  `cancelled_by` INT NULL,

  PRIMARY KEY (`registration_id`),

  UNIQUE KEY `uq_recruiter_event` (`recruiter_id`, `event_id`),

  INDEX `idx_recruiter` (`recruiter_id`),
  INDEX `idx_event` (`event_id`),

  CONSTRAINT `fk_recruiter`
    FOREIGN KEY (`recruiter_id`) REFERENCES `users` (`user_id`),

  CONSTRAINT `fk_event`
    FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`),

  CONSTRAINT `fk_cancelled_by`
    FOREIGN KEY (`cancelled_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB;

##########################################################
# Views
##########################################################

CREATE VIEW approved_registrations AS
SELECT * FROM registrations
WHERE status = 'APPROVED';

CREATE VIEW pending_registrations AS
SELECT * FROM registrations
WHERE status = 'PENDING';

CREATE VIEW cancelled_registrations AS
SELECT * FROM registrations
WHERE status LIKE 'CANCELLED_%';

CREATE VIEW event_info AS
SELECT event_id, event_name, city, state, event_datetime, capacity
FROM events;

##########################################################
# Triggers
##########################################################

DELIMITER $$

CREATE TRIGGER check_recruiter_role
BEFORE INSERT ON registrations
FOR EACH ROW
BEGIN
  DECLARE r VARCHAR(30);

  SELECT role INTO r
  FROM users
  WHERE user_id = NEW.recruiter_id;

  IF r <> 'Recruiter' THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Only recruiters can register';
  END IF;
END$$

CREATE TRIGGER check_event_creator
BEFORE INSERT ON events
FOR EACH ROW
BEGIN
  DECLARE r VARCHAR(30);

  SELECT role INTO r
  FROM users
  WHERE user_id = NEW.created_by;

  IF r NOT IN ('Admin', 'Event Coordinator') THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Invalid event creator role';
  END IF;
END$$

CREATE TRIGGER set_cancel_datetime
BEFORE UPDATE ON registrations
FOR EACH ROW
BEGIN
  IF NEW.status LIKE 'CANCELLED%' AND OLD.status NOT LIKE 'CANCELLED%' THEN
    SET NEW.cancel_datetime = NOW();
  END IF;
END$$

-- FIX: INSERT capacity check
CREATE TRIGGER check_event_capacity_insert
BEFORE INSERT ON registrations
FOR EACH ROW
BEGIN
  DECLARE cap INT;
  DECLARE approved INT;

  SELECT capacity INTO cap FROM events WHERE event_id = NEW.event_id;

  SELECT COUNT(*) INTO approved
  FROM registrations
  WHERE event_id = NEW.event_id AND status = 'APPROVED';

  IF NEW.status = 'APPROVED' AND approved >= cap THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Event is full';
  END IF;
END$$

-- FIX: UPDATE capacity check (IMPORTANT)
CREATE TRIGGER check_event_capacity_update
BEFORE UPDATE ON registrations
FOR EACH ROW
BEGIN
  DECLARE cap INT;
  DECLARE approved INT;

  IF NEW.status = 'APPROVED' AND OLD.status <> 'APPROVED' THEN

    SELECT capacity INTO cap FROM events WHERE event_id = NEW.event_id;

    SELECT COUNT(*) INTO approved
    FROM registrations
    WHERE event_id = NEW.event_id AND status = 'APPROVED';

    IF approved >= cap THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Event is full (approval blocked)';
    END IF;

  END IF;
END$$

DELIMITER ;

##########################################################
# Procedures
##########################################################

DELIMITER $$

CREATE PROCEDURE register_recruiter(
  IN p_recruiter INT,
  IN p_event INT
)
BEGIN
  INSERT INTO registrations (recruiter_id, event_id)
  VALUES (p_recruiter, p_event);
END$$

CREATE PROCEDURE approve_registration(IN p_id INT)
BEGIN
  UPDATE registrations
  SET status = 'APPROVED'
  WHERE registration_id = p_id;
END$$

CREATE PROCEDURE cancel_registration(
  IN p_id INT,
  IN p_user INT,
  IN p_status VARCHAR(50)
)
BEGIN
  UPDATE registrations
  SET status = p_status,
      cancelled_by = p_user
  WHERE registration_id = p_id;
END$$

DELIMITER ;

##########################################################
# Functions
##########################################################

DELIMITER $$

CREATE FUNCTION get_approved_count(pid INT)
RETURNS INT
DETERMINISTIC
BEGIN
  DECLARE c INT;

  SELECT COUNT(*) INTO c
  FROM registrations
  WHERE event_id = pid AND status = 'APPROVED';

  RETURN c;
END$$

CREATE FUNCTION get_available_spots(pid INT)
RETURNS INT
DETERMINISTIC
BEGIN
  DECLARE cap INT;
  DECLARE c INT;

  SELECT capacity INTO cap FROM events WHERE event_id = pid;

  SELECT COUNT(*) INTO c
  FROM registrations
  WHERE event_id = pid AND status = 'APPROVED';

  RETURN cap - c;
END$$

DELIMITER ;

##########################################################
# Cursor Procedure
##########################################################

DELIMITER $$

CREATE PROCEDURE approved_recruiters(IN p_event INT)
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE n VARCHAR(100);
  DECLARE e VARCHAR(100);

  DECLARE cur CURSOR FOR
    SELECT CONCAT(first_name,' ',last_name), email
    FROM users u
    JOIN registrations r ON u.user_id = r.recruiter_id
    WHERE r.event_id = p_event AND r.status = 'APPROVED';

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  OPEN cur;

  loop1: LOOP
    FETCH cur INTO n, e;

    IF done THEN
      LEAVE loop1;
    END IF;

    SELECT n AS name, e AS email;
  END LOOP;

  CLOSE cur;
END$$

DELIMITER ;