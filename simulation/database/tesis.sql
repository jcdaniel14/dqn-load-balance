/*
 Navicat MySQL Data Transfer

 Source Server         : local
 Source Server Type    : MySQL
 Source Server Version : 50731
 Source Host           : 127.0.0.1:3306
 Source Schema         : tesis

 Target Server Type    : MySQL
 Target Server Version : 50731
 File Encoding         : 65001

 Date: 08/09/2021 01:29:32
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for congestion
-- ----------------------------
DROP TABLE IF EXISTS `congestion`;
CREATE TABLE `congestion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `interface_id` int(11) DEFAULT NULL,
  `bw` int(11) DEFAULT NULL,
  `test_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_interface` (`interface_id`),
  KEY `set_id` (`test_id`),
  CONSTRAINT `fk_interface` FOREIGN KEY (`interface_id`) REFERENCES `interface` (`id`),
  CONSTRAINT `fk_test` FOREIGN KEY (`test_id`) REFERENCES `test` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=71 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of congestion
-- ----------------------------
BEGIN;
INSERT INTO `congestion` VALUES (1, 1, 173, 1);
INSERT INTO `congestion` VALUES (2, 2, 92, 1);
INSERT INTO `congestion` VALUES (3, 3, 47, 1);
INSERT INTO `congestion` VALUES (4, 4, 43, 1);
INSERT INTO `congestion` VALUES (5, 5, 33, 1);
INSERT INTO `congestion` VALUES (6, 6, 55, 1);
INSERT INTO `congestion` VALUES (7, 7, 101, 1);
INSERT INTO `congestion` VALUES (8, 8, 101, 1);
INSERT INTO `congestion` VALUES (9, 9, 101, 1);
INSERT INTO `congestion` VALUES (10, 10, 26, 1);
INSERT INTO `congestion` VALUES (11, 11, 51, 1);
INSERT INTO `congestion` VALUES (12, 12, 101, 1);
INSERT INTO `congestion` VALUES (13, 13, 101, 1);
INSERT INTO `congestion` VALUES (14, 14, 51, 1);
INSERT INTO `congestion` VALUES (15, 1, 128, 2);
INSERT INTO `congestion` VALUES (16, 2, 96, 2);
INSERT INTO `congestion` VALUES (17, 3, 48, 2);
INSERT INTO `congestion` VALUES (18, 4, 49, 2);
INSERT INTO `congestion` VALUES (19, 5, 36, 2);
INSERT INTO `congestion` VALUES (20, 6, 35, 2);
INSERT INTO `congestion` VALUES (21, 7, 158, 2);
INSERT INTO `congestion` VALUES (22, 8, 144, 2);
INSERT INTO `congestion` VALUES (23, 9, 130, 2);
INSERT INTO `congestion` VALUES (24, 10, 38, 2);
INSERT INTO `congestion` VALUES (25, 11, 49, 2);
INSERT INTO `congestion` VALUES (26, 12, 142, 2);
INSERT INTO `congestion` VALUES (27, 13, 112, 2);
INSERT INTO `congestion` VALUES (28, 14, 50, 2);
INSERT INTO `congestion` VALUES (29, 1, 190, 3);
INSERT INTO `congestion` VALUES (30, 2, 1, 3);
INSERT INTO `congestion` VALUES (31, 3, 1, 3);
INSERT INTO `congestion` VALUES (32, 4, 1, 3);
INSERT INTO `congestion` VALUES (33, 5, 1, 3);
INSERT INTO `congestion` VALUES (34, 6, 48, 3);
INSERT INTO `congestion` VALUES (35, 7, 164, 3);
INSERT INTO `congestion` VALUES (36, 8, 108, 3);
INSERT INTO `congestion` VALUES (37, 9, 161, 3);
INSERT INTO `congestion` VALUES (38, 10, 37, 3);
INSERT INTO `congestion` VALUES (39, 11, 83, 3);
INSERT INTO `congestion` VALUES (40, 12, 155, 3);
INSERT INTO `congestion` VALUES (41, 13, 161, 3);
INSERT INTO `congestion` VALUES (42, 14, 82, 3);
INSERT INTO `congestion` VALUES (43, 1, 189, 4);
INSERT INTO `congestion` VALUES (44, 2, 1, 4);
INSERT INTO `congestion` VALUES (45, 3, 49, 4);
INSERT INTO `congestion` VALUES (46, 4, 49, 4);
INSERT INTO `congestion` VALUES (47, 5, 48, 4);
INSERT INTO `congestion` VALUES (48, 6, 46, 4);
INSERT INTO `congestion` VALUES (49, 7, 132, 4);
INSERT INTO `congestion` VALUES (50, 8, 131, 4);
INSERT INTO `congestion` VALUES (51, 9, 115, 4);
INSERT INTO `congestion` VALUES (52, 10, 1, 4);
INSERT INTO `congestion` VALUES (53, 11, 59, 4);
INSERT INTO `congestion` VALUES (54, 12, 1, 4);
INSERT INTO `congestion` VALUES (55, 13, 1, 4);
INSERT INTO `congestion` VALUES (56, 14, 1, 4);
INSERT INTO `congestion` VALUES (57, 1, 194, 5);
INSERT INTO `congestion` VALUES (58, 2, 94, 5);
INSERT INTO `congestion` VALUES (59, 3, 46, 5);
INSERT INTO `congestion` VALUES (60, 4, 46, 5);
INSERT INTO `congestion` VALUES (61, 5, 50, 5);
INSERT INTO `congestion` VALUES (62, 6, 60, 5);
INSERT INTO `congestion` VALUES (63, 7, 196, 5);
INSERT INTO `congestion` VALUES (64, 8, 100, 5);
INSERT INTO `congestion` VALUES (65, 9, 100, 5);
INSERT INTO `congestion` VALUES (66, 10, 25, 5);
INSERT INTO `congestion` VALUES (67, 11, 50, 5);
INSERT INTO `congestion` VALUES (68, 12, 100, 5);
INSERT INTO `congestion` VALUES (69, 13, 100, 5);
INSERT INTO `congestion` VALUES (70, 14, 50, 5);
COMMIT;

-- ----------------------------
-- Table structure for interface
-- ----------------------------
DROP TABLE IF EXISTS `interface`;
CREATE TABLE `interface` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `max_capacity` int(255) DEFAULT NULL,
  `router_id` int(11) DEFAULT NULL,
  `activate` int(1) DEFAULT '0',
  `congestion_percentage` int(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_routers` (`router_id`),
  CONSTRAINT `fk_routers` FOREIGN KEY (`router_id`) REFERENCES `router` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of interface
-- ----------------------------
BEGIN;
INSERT INTO `interface` VALUES (1, 'uio1-port1', 200, 1, 1, 95);
INSERT INTO `interface` VALUES (2, 'uio1-port2', 100, 1, 1, 95);
INSERT INTO `interface` VALUES (3, 'uio1-port3', 50, 1, 1, 90);
INSERT INTO `interface` VALUES (4, 'uio1-port4', 50, 1, 1, 90);
INSERT INTO `interface` VALUES (5, 'uio1-port5', 50, 1, 1, 90);
INSERT INTO `interface` VALUES (6, 'uio1-port6', 60, 1, 1, 90);
INSERT INTO `interface` VALUES (7, 'uio2-port1', 200, 2, 1, 95);
INSERT INTO `interface` VALUES (8, 'uio2-port2', 200, 2, 1, 95);
INSERT INTO `interface` VALUES (9, 'gye1-port1', 200, 3, 1, 95);
INSERT INTO `interface` VALUES (10, 'gye1-port2', 50, 3, 1, 90);
INSERT INTO `interface` VALUES (11, 'gye1-port3', 100, 3, 1, 95);
INSERT INTO `interface` VALUES (12, 'gye1-port4', 200, 3, 1, 95);
INSERT INTO `interface` VALUES (13, 'gye2-port1', 200, 4, 1, 95);
INSERT INTO `interface` VALUES (14, 'gye3-port1', 100, 5, 1, 95);
COMMIT;

-- ----------------------------
-- Table structure for router
-- ----------------------------
DROP TABLE IF EXISTS `router`;
CREATE TABLE `router` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `ciudad` char(3) DEFAULT NULL,
  `active` int(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of router
-- ----------------------------
BEGIN;
INSERT INTO `router` VALUES (1, 'router-uio-1', 'uio', 1);
INSERT INTO `router` VALUES (2, 'router-uio-2', 'uio', 1);
INSERT INTO `router` VALUES (3, 'router-gye-1', 'gye', 1);
INSERT INTO `router` VALUES (4, 'router-gye-2', 'gye', 1);
INSERT INTO `router` VALUES (5, 'router-gye-3', 'gye', 1);
COMMIT;

-- ----------------------------
-- Table structure for test
-- ----------------------------
DROP TABLE IF EXISTS `test`;
CREATE TABLE `test` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Records of test
-- ----------------------------
BEGIN;
INSERT INTO `test` VALUES (1, '2 interfaces saturadas');
INSERT INTO `test` VALUES (2, '3 interfaces');
INSERT INTO `test` VALUES (3, '1 interface saturada');
INSERT INTO `test` VALUES (4, '4 interface');
INSERT INTO `test` VALUES (5, '6 interfaces');
COMMIT;

-- ----------------------------
-- View structure for network
-- ----------------------------
DROP VIEW IF EXISTS `network`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `network` AS select `i`.`id` AS `interface_id`,`r`.`name` AS `router`,`i`.`name` AS `interface`,`r`.`ciudad` AS `local`,round((`i`.`max_capacity` * 0.50),0) AS `inicial`,`i`.`max_capacity` AS `capacidad` from (`interface` `i` join `router` `r` on((`r`.`id` = `i`.`router_id`)));

-- ----------------------------
-- View structure for test_cases
-- ----------------------------
DROP VIEW IF EXISTS `test_cases`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `test_cases` AS select 0 AS `test_id`,'' AS `test_name`,`r`.`name` AS `router`,`i`.`id` AS `interface_id`,`i`.`name` AS `interface`,round((`i`.`max_capacity` * 0.50),0) AS `bw`,`r`.`ciudad` AS `local`,`i`.`max_capacity` AS `capacidad`,0 AS `congestionado`,50 AS `busy_percentage`,0 AS `excess`,`i`.`congestion_percentage` AS `congestion_porcentaje` from (`interface` `i` join `router` `r` on((`r`.`id` = `i`.`router_id`))) union select `c`.`test_id` AS `test_id`,`ts`.`name` AS `test_name`,`r`.`name` AS `router`,`i`.`id` AS `interface_id`,`i`.`name` AS `interface`,`c`.`bw` AS `bw`,`r`.`ciudad` AS `local`,`i`.`max_capacity` AS `capacidad`,if((round(((`c`.`bw` / `i`.`max_capacity`) * 100),0) >= `i`.`congestion_percentage`),1,0) AS `congestionado`,round(((`c`.`bw` / `i`.`max_capacity`) * 100),0) AS `busy_percentage`,if((round(((`c`.`bw` / `i`.`max_capacity`) * 100),0) >= `i`.`congestion_percentage`),(round(((`c`.`bw` / `i`.`max_capacity`) * 100),0) - `i`.`congestion_percentage`),0) AS `excess`,`i`.`congestion_percentage` AS `congestion_porcentaje` from (((`congestion` `c` join `interface` `i` on((`i`.`id` = `c`.`interface_id`))) join `router` `r` on((`r`.`id` = `i`.`router_id`))) join `test` `ts` on((`ts`.`id` = `c`.`test_id`))) order by `test_id`,`local` desc,`interface`,`interface_id`;

SET FOREIGN_KEY_CHECKS = 1;
