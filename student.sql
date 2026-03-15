-- SQL dump for XAMPP MySQL
-- Creates `student` database and required tables used by the Flask app

-- Create database (safe to run multiple times)
CREATE DATABASE IF NOT EXISTS `student` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `student`;

-- ----------------------------------------------------------------------
-- Core table required by app/app.py (/register and /download_students)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `student_info` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(100) NOT NULL,
  `RegisterNum` VARCHAR(50) NOT NULL,
  `Department` VARCHAR(100) NOT NULL,
  `Bikeno` VARCHAR(32) NOT NULL,
  `MobileNum` VARCHAR(20) NOT NULL,
  `Email` VARCHAR(120) NOT NULL,
  `CreatedAt` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_regnum` (`RegisterNum`),
  UNIQUE KEY `uniq_email` (`Email`),
  KEY `idx_name` (`Name`),
  KEY `idx_department` (`Department`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------------
-- Optional tables (not strictly required by current app/app.py routes)
-- Kept for future expansion and admin usage.
-- ----------------------------------------------------------------------

-- Users table (alternative student registrations model)
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `roll_no` VARCHAR(50) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(120) NOT NULL,
  `phone` VARCHAR(20) DEFAULT NULL,
  `department` VARCHAR(100) DEFAULT NULL,
  `year` VARCHAR(20) DEFAULT NULL,
  `section` VARCHAR(10) DEFAULT NULL,
  `photo_path` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_roll_no` (`roll_no`),
  UNIQUE KEY `uniq_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Admins table (admin login)
CREATE TABLE IF NOT EXISTS `admins` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(80) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Vehicles table (optional mapping from student to plate and picture)
CREATE TABLE IF NOT EXISTS `vehicles` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `plate_number` VARCHAR(32) NOT NULL,
  `vehicle_type` VARCHAR(50) DEFAULT NULL,
  `picture_path` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_plate` (`plate_number`),
  KEY `fk_vehicle_user` (`user_id`),
  CONSTRAINT `fk_vehicle_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Detections table (results from processing)
CREATE TABLE IF NOT EXISTS `detections` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED DEFAULT NULL,
  `plate_number` VARCHAR(32) DEFAULT NULL,
  `helmet` TINYINT(1) NOT NULL DEFAULT 0, -- 1=helmet, 0=no-helmet
  `confidence` DECIMAL(5,4) DEFAULT NULL,
  `image_path` VARCHAR(255) DEFAULT NULL,
  `captured_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_plate` (`plate_number`),
  KEY `idx_captured_at` (`captured_at`),
  KEY `fk_detection_user` (`user_id`),
  CONSTRAINT `fk_detection_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Defaulters table (students marked without helmet)
CREATE TABLE IF NOT EXISTS `defaulters` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED DEFAULT NULL,
  `plate_number` VARCHAR(32) DEFAULT NULL,
  `reason` VARCHAR(255) DEFAULT 'No Helmet',
  `image_path` VARCHAR(255) DEFAULT NULL,
  `detected_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_defaulter_plate` (`plate_number`),
  KEY `fk_defaulter_user` (`user_id`),
  CONSTRAINT `fk_defaulter_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Audit table (optional)
CREATE TABLE IF NOT EXISTS `audit_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `event` VARCHAR(50) NOT NULL,
  `actor` VARCHAR(120) DEFAULT NULL,
  `meta` JSON DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_event_time` (`event`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed a default admin (username: admin, password: admin)
-- Replace password hash in production!
INSERT INTO `admins` (`username`, `password_hash`)
VALUES
('admin', '$2b$12$KIXQf5pQfM4GxkG4d9N/7u3xG2Qp7R0m5mSa4x4J6a3a0d1o2h6lS')
ON DUPLICATE KEY UPDATE username = VALUES(username);
