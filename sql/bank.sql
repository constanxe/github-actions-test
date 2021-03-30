-- SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+08:00";

--
-- Database: `cs301_team1_bank`
--

DROP SCHEMA IF EXISTS `cs301_team1_bank`;
CREATE SCHEMA `cs301_team1_bank`;
-- CREATE SCHEMA IF NOT EXISTS `cs301_team1_bank`;
USE `cs301_team1_bank`; 

-- --------------------------------------------------------

--
-- Table structure for table `bank_user`
--

DROP TABLE IF EXISTS `bank_user`;
CREATE TABLE IF NOT EXISTS `bank_user` (
  `user_id` varchar(120) NOT NULL,
  `username` varchar(80) NOT NULL,
  `firstname` varchar(80) NOT NULL,
  `lastname` varchar(80) NOT NULL,
  `password` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `points` int(10) NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `bank_user` (`user_id`, `username`, `firstname`, `lastname`, `password`, `email`, `points`) VALUES
('iG79s45QEeu80dRtbaI6YA==', 'user1', 'user', 'one', 'userone', 'userone@gamil.com', 500000),
('kpa63Y5QEeuYUdRtbaI6YA==', 'user2', 'user', 'two', 'usertwo', 'usertwo@gamil.com', 500000),
('oVt5F45QEeuQrdRtbaI6YA==', 'admin1', 'admin', 'one', 'adminone', 'adminone@gamil.com', 500000);

-- --------------------------------------------------------

--
-- Table structure for table `bank_user`
--

DROP TABLE IF EXISTS `bank_loyalty_user`;
CREATE TABLE IF NOT EXISTS `bank_loyalty_user` (
  `id` int not null AUTO_INCREMENT,
  `user_id` varchar(120) NOT NULL,
  `loyalty_id` varchar(80) NOT NULL,
  `member_id` varchar(80) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

-- 
-- Table structure for table `bank_transaction`
-- 

DROP TABLE IF EXISTS `bank_transaction`;
CREATE TABLE IF NOT EXISTS `bank_transaction` (
  `reference_num` varchar(120) NOT NULL,
  `loyalty_id` varchar(120) NOT NULL,
  `user_id` varchar(120) NOT NULL,
  `member_id` varchar(120) NOT NULL,
  `transaction_date` varchar(10) NOT NULL,
  `amount` int(10) NOT NULL,
  `additional_info` varchar(1000) DEFAULT NULL,
  `outcome_code` int(4) DEFAULT NULL,
  PRIMARY KEY (`reference_num`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `bank_transaction` (`reference_num`, `loyalty_id`, `user_id`, `member_id`, `transaction_date`, `amount`, `additional_info`, `outcome_code`) 
  VALUES ('1', 'GRABPOINTS', '2', '3', '2021-02-10 12:12:00', '100', '', ''), 
          ('2', 'PASSIONPOINTS', '3', '4', '2021-02-06 23:45:00', '5', '', ''), 
          ('3', 'GOPOINTS', '1', '2', '2021-02-16 13:45:00', '90', '', ''), 
          ('4', 'KRISPOINTS', '5', '5', '2021-02-10 10:00:00', '40', '', '');