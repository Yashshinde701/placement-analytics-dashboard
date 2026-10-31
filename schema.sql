-- MySQL 8.0.16+ (earlier versions parse CHECK but do not enforce it).
CREATE DATABASE IF NOT EXISTS placement_db CHARACTER SET utf8mb4;
USE placement_db;

CREATE TABLE students (
  student_id          VARCHAR(10)      PRIMARY KEY,
  branch              VARCHAR(20)      NOT NULL,
  cgpa                DECIMAL(4,2)     NOT NULL CHECK (cgpa BETWEEN 0 AND 10),
  backlogs            TINYINT UNSIGNED NOT NULL,
  internships         TINYINT UNSIGNED NOT NULL,
  projects            TINYINT UNSIGNED NOT NULL,
  certifications      TINYINT UNSIGNED NOT NULL,
  aptitude_score      DECIMAL(4,1)     NOT NULL CHECK (aptitude_score BETWEEN 0 AND 100),
  communication_score DECIMAL(4,1)     NOT NULL CHECK (communication_score BETWEEN 0 AND 100),
  skills              VARCHAR(100)     NOT NULL DEFAULT '',
  shortlisted         TINYINT(1)       NOT NULL CHECK (shortlisted IN (0, 1))
) ENGINE=InnoDB;
