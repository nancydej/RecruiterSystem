-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE,
SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

DROP SCHEMA IF EXISTS `group5`;
CREATE SCHEMA IF NOT EXISTS `group5` DEFAULT CHARACTER SET utf8;
USE `group5`;

##########################################################
# Table: usersevents
##########################################################

CREATE TABLE IF NOT EXISTS `group5`.`users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `first_name` VARCHAR(50) NULL,
  `last_name` VARCHAR(50) NULL,
  `email` VARCHAR(100) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `phone_number` VARCHAR(15) NOT NULL,
  `role` ENUM('Admin', 'Event Coordinator', 'Recruiter') NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  INDEX `idx_role` (`role` ASC) VISIBLE
)
ENGINE = InnoDB;

##########################################################
# Table: events
##########################################################

CREATE TABLE IF NOT EXISTS `group5`.`events` (
  `event_id` INT NOT NULL AUTO_INCREMENT,
  `created_by` INT NOT NULL,
  `event_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `city` VARCHAR(50) NOT NULL,
  `state` VARCHAR(50) NOT NULL,
  `event_datetime` DATETIME NOT NULL,
  `capacity` INT NOT NULL,
  PRIMARY KEY (`event_id`),
  INDEX `createdbyfk_idx` (`created_by` ASC) VISIBLE,
  INDEX `idx_eventdate` (`event_datetime` ASC) VISIBLE,
  CONSTRAINT `fk_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `group5`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_capacity_range`
    CHECK (`capacity` BETWEEN 3 AND 10)
)
ENGINE = InnoDB;

##########################################################
# Table: registrations
##########################################################

CREATE TABLE IF NOT EXISTS `group5`.`registrations` (
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
  INDEX `recruiterfk_idx` (`recruiter_id` ASC) VISIBLE,
  INDEX `eventfk_idx` (`event_id` ASC) VISIBLE,
  INDEX `cancelledbyfk_idx` (`cancelled_by` ASC) VISIBLE,
  UNIQUE INDEX `idx_recruiter_event` (`recruiter_id` ASC, `event_id` ASC) VISIBLE,
  CONSTRAINT `fk_recruiter_id`
    FOREIGN KEY (`recruiter_id`)
    REFERENCES `group5`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_event_id`
    FOREIGN KEY (`event_id`)
    REFERENCES `group5`.`events` (`event_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_cancelled_by`
    FOREIGN KEY (`cancelled_by`)
    REFERENCES `group5`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
ENGINE = InnoDB;


##########################################################
# VIEW 1: Approved Registrations
##########################################################

CREATE VIEW `group5`.`approved_registrations` AS
SELECT
  `registration_id`,
  `recruiter_id`,
  `event_id`,
  `status`,
  `registration_datetime`
FROM `group5`.`registrations`
WHERE `status` = 'APPROVED';


##########################################################
# VIEW 2: Pending Registrations
##########################################################

CREATE VIEW `group5`.`pending_registrations` AS
SELECT
  `registration_id`,
  `recruiter_id`,
  `event_id`,
  `status`,
  `registration_datetime`
FROM `group5`.`registrations`
WHERE `status` = 'PENDING';


##########################################################
# VIEW 3: Cancelled Registrations
##########################################################

CREATE VIEW `group5`.`cancelled_registrations` AS
SELECT
  `registration_id`,
  `recruiter_id`,
  `event_id`,
  `status`,
  `registration_datetime`,
  `cancel_datetime`,
  `cancelled_by`
FROM `group5`.`registrations`
WHERE `status` IN (
  'CANCELLED_FULL_REFUND',
  'CANCELLED_PARTIAL_REFUND',
  'CANCELLED_NO_REFUND'
);


##########################################################
# VIEW 4: Event Info
##########################################################

CREATE VIEW `group5`.`event_info` AS
SELECT
  `event_id`,
  `event_name`,
  `city`,
  `state`,
  `event_datetime`,
  `capacity`
FROM `group5`.`events`;


##########################################################
# TRIGGER 1: Check recruiter role before registration
##########################################################

DELIMITER $$

CREATE TRIGGER `group5`.`check_recruiter_role`
BEFORE INSERT ON `group5`.`registrations`
FOR EACH ROW
BEGIN
  DECLARE user_role VARCHAR(30);

  SELECT `role`
  INTO user_role
  FROM `group5`.`users`
  WHERE `user_id` = NEW.`recruiter_id`;

  IF user_role <> 'Recruiter' THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Only recruiters can register for events';
  END IF;
END$$


##########################################################
# TRIGGER 2: Set cancel datetime automatically
##########################################################

CREATE TRIGGER `group5`.`set_cancel_datetime`
BEFORE UPDATE ON `group5`.`registrations`
FOR EACH ROW
BEGIN
  IF NEW.`status` LIKE 'CANCELLED%' AND OLD.`status` NOT LIKE 'CANCELLED%' THEN
    SET NEW.`cancel_datetime` = NOW();
  END IF;
END$$


##########################################################
# TRIGGER 3: Check event creator role
##########################################################

CREATE TRIGGER `group5`.`check_event_creator`
BEFORE INSERT ON `group5`.`events`
FOR EACH ROW
BEGIN
  DECLARE creator_role VARCHAR(30);

  SELECT `role`
  INTO creator_role
  FROM `group5`.`users`
  WHERE `user_id` = NEW.`created_by`;

  IF creator_role <> 'Admin' AND creator_role <> 'Event Coordinator' THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Only Admin or Event Coordinator can create events';
  END IF;
END$$


##########################################################
# TRIGGER 4: Check event capacity
##########################################################

CREATE TRIGGER `group5`.`check_event_capacity`
BEFORE INSERT ON `group5`.`registrations`
FOR EACH ROW
BEGIN
  DECLARE approved_count INT;
  DECLARE max_capacity INT;

  SELECT COUNT(*)
  INTO approved_count
  FROM `group5`.`registrations`
  WHERE `event_id` = NEW.`event_id`
    AND `status` = 'APPROVED';

  SELECT `capacity`
  INTO max_capacity
  FROM `group5`.`events`
  WHERE `event_id` = NEW.`event_id`;

  IF NEW.`status` = 'APPROVED' AND approved_count >= max_capacity THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Event is already full';
  END IF;
END$$

#############################################################
# PROCEDURE 1: Register a recruiter for an event
#############################################################

DELIMITER $$

CREATE PROCEDURE `group5`.`register_recruiter_for_event`(
    IN p_recruiter_id INT,
    IN p_event_id INT
)
BEGIN
    INSERT INTO `group5`.`registrations` (
        recruiter_id,
        event_id,
        status,
        registration_datetime
    )
    VALUES (
        p_recruiter_id,
        p_event_id,
        'PENDING',
        NOW()
    );
END$$

DELIMITER ;


#############################################################
# PROCEDURE 2: Approve a registration
#############################################################

DELIMITER $$

CREATE PROCEDURE `group5`.`approve_registration`(
    IN p_registration_id INT
)
BEGIN
    UPDATE `group5`.`registrations`
    SET status = 'APPROVED'
    WHERE registration_id = p_registration_id;
END$$

DELIMITER ;


#############################################################
# PROCEDURE 3: Cancel a registration
#############################################################

DELIMITER $$

CREATE PROCEDURE `group5`.`cancel_registration`(
    IN p_registration_id INT,
    IN p_cancelled_by INT,
    IN p_cancel_status VARCHAR(50)
)
BEGIN
    UPDATE `group5`.`registrations`
    SET
        status = p_cancel_status,
        cancelled_by = p_cancelled_by
    WHERE registration_id = p_registration_id;
END$$

DELIMITER ;


#############################################################
# FUNCTION 1: Get number of approved registrations
#############################################################

DELIMITER $$

CREATE FUNCTION `group5`.`get_approved_count`(
    p_event_id INT
)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE approved_count INT;

    SELECT COUNT(*)
    INTO approved_count
    FROM `group5`.`registrations`
    WHERE event_id = p_event_id
    AND status = 'APPROVED';

    RETURN approved_count;
END$$

DELIMITER ;


#############################################################
# FUNCTION 2: Get available spots for an event
#############################################################

DELIMITER $$

CREATE FUNCTION `group5`.`get_available_spots`(
    p_event_id INT
)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE event_capacity INT;
    DECLARE approved_count INT;
    DECLARE spots_left INT;

    SELECT capacity
    INTO event_capacity
    FROM `group5`.`events`
    WHERE event_id = p_event_id;

    SELECT COUNT(*)
    INTO approved_count
    FROM `group5`.`registrations`
    WHERE event_id = p_event_id
    AND status = 'APPROVED';

    SET spots_left = event_capacity - approved_count;

    RETURN spots_left;
END$$

DELIMITER ;


#############################################################
# CURSOR PROCEDURE: Show approved recruiters for one event
#############################################################

DELIMITER $$

CREATE PROCEDURE `group5`.`show_approved_recruiters_for_event`(
    IN p_event_id INT
)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE recruiter_name VARCHAR(150);
    DECLARE recruiter_email VARCHAR(100);

    DECLARE recruiter_cursor CURSOR FOR
        SELECT
            CONCAT(u.first_name, ' ', u.last_name),
            u.email
        FROM `group5`.`users` u
        JOIN `group5`.`registrations` r
        ON u.user_id = r.recruiter_id
        WHERE r.event_id = p_event_id
        AND r.status = 'APPROVED';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN recruiter_cursor;

    read_loop: LOOP
        FETCH recruiter_cursor INTO recruiter_name, recruiter_email;

        IF done = 1 THEN
            LEAVE read_loop;
        END IF;

        SELECT
            recruiter_name AS approved_recruiter,
            recruiter_email AS email;
    END LOOP;

    CLOSE recruiter_cursor;
END$$

DELIMITER ;