-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema group5
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema group5
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `group5` DEFAULT CHARACTER SET utf8 ;
USE `group5` ;

-- -----------------------------------------------------
-- Table `group5`.`users`
-- -----------------------------------------------------
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
  UNIQUE INDEX `user_id_UNIQUE` (`user_id` ASC) VISIBLE,
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  INDEX `idx_role` (`role` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `group5`.`events`
-- -----------------------------------------------------
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
  UNIQUE INDEX `event_id_UNIQUE` (`event_id` ASC) VISIBLE,
  INDEX `createdbyfk_idx` (`created_by` ASC) VISIBLE,
  INDEX `idx_eventdate` (`event_datetime` ASC) INVISIBLE,
  CONSTRAINT `fk_created_by`
    FOREIGN KEY (`created_by`)
    REFERENCES `group5`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `group5`.`registrations`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `group5`.`registrations` (
  `registration_id` INT NOT NULL AUTO_INCREMENT,
  `recruiter_id` INT NOT NULL,
  `event_id` INT NOT NULL,
  `status` ENUM('PENDING', 'APPROVED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
  `registration_datetime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cancel_datetime` DATETIME NULL,
  `cancelled_by` INT NULL,
  PRIMARY KEY (`registration_id`),
  UNIQUE INDEX `registration_id_UNIQUE` (`registration_id` ASC) VISIBLE,
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
    ON UPDATE NO ACTION)
ENGINE = InnoDB;
ALTER TABLE events ADD CONSTRAINT chk_capacity CHECK (capacity > 0);

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
