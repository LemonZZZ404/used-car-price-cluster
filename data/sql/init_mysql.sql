-- ============================================================
-- 二手车价格评估系统 - MySQL建表脚本
-- 数据库：used_car
-- ============================================================

CREATE DATABASE IF NOT EXISTS used_car DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE used_car;

-- -----------------------------------------------------------
-- 1. 二手车原始信息表（业务基础数据）
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `car_info`;
CREATE TABLE `car_info` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `car_id`        VARCHAR(64)  NOT NULL COMMENT '车辆唯一编号',
  `brand`         VARCHAR(64)  NOT NULL COMMENT '品牌',
  `series`        VARCHAR(128) DEFAULT NULL COMMENT '车系',
  `model`         VARCHAR(256) DEFAULT NULL COMMENT '车型',
  `price`         DECIMAL(12,2) NOT NULL COMMENT '售价（万元）',
  `original_price` DECIMAL(12,2) DEFAULT NULL COMMENT '新车指导价（万元）',
  `age`           INT          DEFAULT NULL COMMENT '车龄（年）',
  `mileage`       DECIMAL(10,2) DEFAULT NULL COMMENT '里程（万公里）',
  `gearbox`       VARCHAR(32)  DEFAULT NULL COMMENT '变速箱：手动/自动',
  `displacement`  VARCHAR(32)  DEFAULT NULL COMMENT '排量',
  `fuel_type`     VARCHAR(32)  DEFAULT NULL COMMENT '燃油类型',
  `color`         VARCHAR(32)  DEFAULT NULL COMMENT '车身颜色',
  `city`          VARCHAR(64)  DEFAULT NULL COMMENT '所在城市',
  `register_date` DATE         DEFAULT NULL COMMENT '上牌日期',
  `inspection_date` DATE       DEFAULT NULL COMMENT '年检到期',
  `insurance_date` DATE        DEFAULT NULL COMMENT '保险到期',
  `create_time`   DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_car_id` (`car_id`),
  KEY `idx_brand` (`brand`),
  KEY `idx_city` (`city`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='二手车车辆信息表';

-- -----------------------------------------------------------
-- 2. Spark分析结果表 - 品牌均价统计
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `stat_brand_price`;
CREATE TABLE `stat_brand_price` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `brand`       VARCHAR(64)  NOT NULL COMMENT '品牌',
  `car_count`   INT          DEFAULT 0 COMMENT '车辆数量',
  `avg_price`   DECIMAL(12,2) DEFAULT NULL COMMENT '平均售价（万元）',
  `min_price`   DECIMAL(12,2) DEFAULT NULL COMMENT '最低售价',
  `max_price`   DECIMAL(12,2) DEFAULT NULL COMMENT '最高售价',
  `update_time` DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_brand` (`brand`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌价格统计表';

-- -----------------------------------------------------------
-- 3. Spark分析结果表 - 车龄均价统计
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `stat_age_price`;
CREATE TABLE `stat_age_price` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `age`         INT          NOT NULL COMMENT '车龄（年）',
  `car_count`   INT          DEFAULT 0 COMMENT '车辆数量',
  `avg_price`   DECIMAL(12,2) DEFAULT NULL COMMENT '平均售价',
  `update_time` DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_age` (`age`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='车龄价格统计表';

-- -----------------------------------------------------------
-- 4. Spark分析结果表 - 价格分布统计
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `stat_price_distribution`;
CREATE TABLE `stat_price_distribution` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `price_range` VARCHAR(64)  NOT NULL COMMENT '价格区间，如 0-5万',
  `car_count`   INT          DEFAULT 0 COMMENT '该区间车辆数',
  `update_time` DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_range` (`price_range`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='价格分布统计表';

-- -----------------------------------------------------------
-- 5. 预测记录表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `prediction_record`;
CREATE TABLE `prediction_record` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT,
  `brand`         VARCHAR(64)  NOT NULL COMMENT '品牌',
  `age`           INT          NOT NULL COMMENT '车龄',
  `mileage`       DECIMAL(10,2) NOT NULL COMMENT '里程（万公里）',
  `gearbox`       VARCHAR(32)  DEFAULT NULL COMMENT '变速箱',
  `displacement`  VARCHAR(32)  DEFAULT NULL COMMENT '排量',
  `fuel_type`     VARCHAR(32)  DEFAULT NULL COMMENT '燃油类型',
  `predicted_price` DECIMAL(12,2) NOT NULL COMMENT '预测价格（万元）',
  `model_type`    VARCHAR(32)  DEFAULT 'sklearn' COMMENT '模型类型：sklearn/spark_mllib',
  `create_time`   DATETIME     DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_brand` (`brand`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='价格预测记录表';

-- -----------------------------------------------------------
-- 6. 系统用户表（简单管理）
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT,
  `username`    VARCHAR(64)  NOT NULL,
  `password`    VARCHAR(128) NOT NULL,
  `role`        VARCHAR(32)  DEFAULT 'user',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 默认管理员 admin/admin123
INSERT INTO `sys_user` (`username`, `password`, `role`) VALUES
('admin', 'pbkdf2_sha256$260000$abcdefghijklmnopqrstuvwxyz0123456789$hashedpasswordplaceholder', 'admin');
