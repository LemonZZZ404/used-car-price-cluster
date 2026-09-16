-- ============================================================
-- Hive 建表脚本 - 二手车价格评估系统
-- 数据库：used_car
-- ============================================================

CREATE DATABASE IF NOT EXISTS used_car COMMENT '二手车价格评估数据库';
USE used_car;

-- -----------------------------------------------------------
-- 1. 原始数据表（外部表，指向HDFS原始数据目录）
-- -----------------------------------------------------------
DROP TABLE IF EXISTS used_car.ods_car_info;
CREATE EXTERNAL TABLE used_car.ods_car_info (
  car_id        STRING  COMMENT '车辆编号',
  brand         STRING  COMMENT '品牌',
  series        STRING  COMMENT '车系',
  model         STRING  COMMENT '车型',
  price         DOUBLE  COMMENT '售价（万元）',
  original_price DOUBLE COMMENT '新车指导价',
  age           INT     COMMENT '车龄（年）',
  mileage       DOUBLE  COMMENT '里程（万公里）',
  gearbox       STRING  COMMENT '变速箱',
  displacement  STRING  COMMENT '排量',
  fuel_type     STRING  COMMENT '燃油类型',
  color         STRING  COMMENT '颜色',
  city          STRING  COMMENT '城市',
  register_date STRING  COMMENT '上牌日期'
)
COMMENT '二手车原始数据表'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/used_car/ods/ods_car_info'
TBLPROPERTIES ('skip.header.line.count'='1');

-- -----------------------------------------------------------
-- 2. 清洗后明细表（分区表，按品牌分区，ORC存储）
-- -----------------------------------------------------------
DROP TABLE IF EXISTS used_car.dwd_car_info;
CREATE TABLE used_car.dwd_car_info (
  car_id        STRING  COMMENT '车辆编号',
  brand         STRING  COMMENT '品牌',
  series        STRING  COMMENT '车系',
  model         STRING  COMMENT '车型',
  price         DOUBLE  COMMENT '售价（万元）',
  original_price DOUBLE COMMENT '新车指导价',
  age           INT     COMMENT '车龄（年）',
  mileage       DOUBLE  COMMENT '里程（万公里）',
  gearbox       STRING  COMMENT '变速箱',
  displacement  STRING  COMMENT '排量',
  fuel_type     STRING  COMMENT '燃油类型',
  color         STRING  COMMENT '颜色',
  city          STRING  COMMENT '城市',
  register_date STRING  COMMENT '上牌日期',
  price_level   STRING  COMMENT '价格区间标签',
  depreciation_rate DOUBLE COMMENT '折旧率'
)
COMMENT '二手车清洗后明细表'
PARTITIONED BY (dt STRING COMMENT '数据日期')
STORED AS ORC
LOCATION '/user/hive/warehouse/used_car/dwd/dwd_car_info'
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- -----------------------------------------------------------
-- 3. 品牌价格汇总表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS used_car.ads_brand_price;
CREATE TABLE used_car.ads_brand_price (
  brand       STRING  COMMENT '品牌',
  car_count   BIGINT  COMMENT '车辆数量',
  avg_price   DOUBLE  COMMENT '平均售价',
  min_price   DOUBLE  COMMENT '最低售价',
  max_price   DOUBLE  COMMENT '最高售价',
  std_price   DOUBLE  COMMENT '价格标准差'
)
COMMENT '品牌价格汇总表'
STORED AS ORC
LOCATION '/user/hive/warehouse/used_car/ads/ads_brand_price';

-- -----------------------------------------------------------
-- 4. 车龄价格汇总表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS used_car.ads_age_price;
CREATE TABLE used_car.ads_age_price (
  age         INT     COMMENT '车龄',
  car_count   BIGINT  COMMENT '车辆数量',
  avg_price   DOUBLE  COMMENT '平均售价',
  avg_mileage DOUBLE  COMMENT '平均里程'
)
COMMENT '车龄价格汇总表'
STORED AS ORC
LOCATION '/user/hive/warehouse/used_car/ads/ads_age_price';

-- -----------------------------------------------------------
-- 5. 价格分布表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS used_car.ads_price_distribution;
CREATE TABLE used_car.ads_price_distribution (
  price_range STRING  COMMENT '价格区间',
  car_count   BIGINT  COMMENT '车辆数量',
  ratio       DOUBLE  COMMENT '占比'
)
COMMENT '价格分布表'
STORED AS ORC
LOCATION '/user/hive/warehouse/used_car/ads/ads_price_distribution';

-- -----------------------------------------------------------
-- 6. 日志表（Flume采集的访问日志）
-- -----------------------------------------------------------
DROP TABLE IF EXISTS used_car.ods_access_log;
CREATE EXTERNAL TABLE used_car.ods_access_log (
  log_time    STRING  COMMENT '日志时间',
  ip          STRING  COMMENT '客户端IP',
  method      STRING  COMMENT '请求方法',
  url         STRING  COMMENT '请求URL',
  status      INT     COMMENT '响应状态码',
  user_agent  STRING  COMMENT '用户代理'
)
COMMENT '系统访问日志表'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '|'
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/used_car/ods/ods_access_log';

-- ============================================================
-- 验证
-- ============================================================
SHOW TABLES IN used_car;
