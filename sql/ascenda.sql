SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+08:00";

--
-- Database: `cs301_team1_ascenda`
--

DROP SCHEMA IF EXISTS `cs301_team1_ascenda`;
CREATE SCHEMA `cs301_team1_ascenda`;
-- CREATE SCHEMA IF NOT EXISTS `cs301_team1_ascenda`;
USE `cs301_team1_ascenda`;

-- --------------------------------------------------------

--
-- Table structure for table `ascenda_transaction`
--

DROP TABLE IF EXISTS `ascenda_transaction`;
CREATE TABLE `ascenda_transaction` (
  `id` varchar(120) NOT NULL,
  `loyalty_id` varchar(120) NOT NULL,
  `member_id` varchar(120) NOT NULL,
  `member_name_first` varchar(80) NOT NULL,
  `member_name_last` varchar(80) NOT NULL,
  `transaction_date` varchar(10) NOT NULL,
  `amount` int(10) NOT NULL,
  `reference_num` varchar(120) NOT NULL,
  `partner_code` varchar(120) NOT NULL,
  `bank_user_id` varchar(120) NOT NULL,
  `additional_info` varchar(1000) DEFAULT NULL,
  `outcome_code` int(4) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `ascenda_exchange_rate`
--

DROP TABLE IF EXISTS `ascenda_exchange_rate`;
CREATE TABLE IF NOT EXISTS `ascenda_exchange_rate` (
  `bank_id` varchar(120) NOT NULL,
  `loyalty_id` varchar(120) NOT NULL,
  `base_exchange_amount` float(10) NOT NULL,
  `loyalty_exchange_amount` float(10) NOT NULL,
  PRIMARY KEY (`bank_id`, `loyalty_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `ascenda_exchange_rate` (`bank_id`, `loyalty_id`, `base_exchange_amount`, `loyalty_exchange_amount`) 
  VALUES ('DBSBANK', 'GOPOINTS', '1', '100'), 
          ('DBSBANK', 'GRABPOINTS', '10', '1'), 
          ('DBSBANK', 'PASSIONPOINTS', '3', '10'), 
          ('DBSBANK', 'KRISPOINTS', '50', '1'), 
          ('DBSBANK', 'CHOOPOINTS', '4', '5'), 
          ('DBSBANK', 'BLOOPPOINTS', '3', '20');

-- --------------------------------------------------------

--
-- Table structure for table `ascenda_bank`
--

DROP TABLE IF EXISTS `ascenda_bank`;
CREATE TABLE IF NOT EXISTS `ascenda_bank` (
  `bank_id` varchar(120) NOT NULL,
  `bank_name` varchar(120) NOT NULL,
  `bank_unit` varchar(120) NOT NULL,
  PRIMARY KEY (`bank_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `ascenda_bank` (`bank_id`, `bank_name`, `bank_unit`) 
  VALUES ('DBSBANK', 'DBS Bank', 'DbsPoints');

-- --------------------------------------------------------

--
-- Table structure for table `ascenda_loyalty`
--

DROP TABLE IF EXISTS `ascenda_loyalty`;
CREATE TABLE IF NOT EXISTS `ascenda_loyalty` (
  `loyalty_id` varchar(120) NOT NULL,
  `loyalty_name` varchar(120) NOT NULL,
  `loyalty_unit` varchar(120) NOT NULL,
  `processing_time` varchar(120) NOT NULL,
  `description` varchar(120) NOT NULL,
  `enrollment_link` varchar(120) NOT NULL,
  `terms_link` varchar(120) NOT NULL,
  `validation` varchar(120) DEFAULT NULL,
  PRIMARY KEY (`loyalty_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `ascenda_loyalty` (`loyalty_id`, `loyalty_name`, `loyalty_unit`, `processing_time`, `description`, `enrollment_link`, `terms_link`, `validation`) 
  VALUES ('GOPOINTS', 'GoJet Points', 'GoPoints', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{10}|\\d{16}$'), 
          ('INDOPACIFIC', 'IndoPacific Miles', 'IndoPacific', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{10}$'),   
          ('EMINENT', 'Eminent Airways Guest', 'Eminent', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{12}$'), 
          ('QUANTUM', 'Quantum Airlines QFlyer', 'Quantum', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{10}$'), 
          ('CONRAD', 'Conrad X Club', 'Conrad', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{9}$'), 
          ('MILLENNIUM', 'Millennium Rewards', 'Millennium', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{10}[A-Z]$'),
          ('GRABPOINTS', 'Grab Points', 'GrabPoints', 'instant', 'description', 'www.google.com', 'www.google.com', '^\\d{10}$');
-- --------------------------------------------------------

--
-- Table structure for table `ascenda_file_name`
--

DROP TABLE IF EXISTS `ascenda_file_name`;
CREATE TABLE `ascenda_file_name` (
  `reference_num` varchar(120) NOT NULL,
  `file_name` varchar(120) NOT NULL,
  PRIMARY KEY (`file_name`, `reference_num`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `ascenda_file_name` (`reference_num`, `file_name`) 
  VALUES ('1', 'AL_20210311');
