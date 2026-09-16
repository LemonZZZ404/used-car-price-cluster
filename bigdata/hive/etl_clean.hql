-- ============================================================
-- Hive ETL 清洗脚本
-- 流程：ods_car_info -> 数据清洗 -> dwd_car_info -> 汇总统计
-- 用法：hive -f etl_clean.hql --hivevar dt=20240101
-- ============================================================

USE used_car;

-- 设置动态分区
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=1000;
SET hive.exec.max.dynamic.partitions.pernode=500;

-- ============================================================
-- 第一步：ODS -> DWD 数据清洗
-- ============================================================
INSERT OVERWRITE TABLE used_car.dwd_car_info PARTITION (dt='${hivevar:dt}')
SELECT
    car_id,
    TRIM(brand)                          AS brand,
    TRIM(series)                         AS series,
    TRIM(model)                          AS model,
    price,
    original_price,
    age,
    mileage,
    -- 变速箱标准化
    CASE
        WHEN gearbox IN ('手动', 'MT', '手动挡') THEN '手动'
        ELSE '自动'
    END                                  AS gearbox,
    -- 排量标准化
    CASE
        WHEN displacement IS NULL OR displacement = '' THEN '2.0L'
        ELSE displacement
    END                                  AS displacement,
    -- 燃油类型标准化
    CASE
        WHEN fuel_type IN ('纯电动', '电动', 'EV', 'BEV') THEN '纯电动'
        WHEN fuel_type IN ('混动', '混合动力', 'HEV') THEN '混合动力'
        WHEN fuel_type IN ('插电混动', 'PHEV') THEN '插电混动'
        WHEN fuel_type IN ('柴油', 'Diesel') THEN '柴油'
        ELSE '汽油'
    END                                  AS fuel_type,
    -- 颜色填充
    CASE WHEN color IS NULL OR color = '' OR color = 'nan' THEN '其他' ELSE color END AS color,
    -- 城市填充
    CASE WHEN city IS NULL OR city = '' OR city = 'nan' THEN '未知' ELSE city END AS city,
    register_date,
    -- 价格区间标签
    CASE
        WHEN price < 5   THEN '0-5万'
        WHEN price < 10  THEN '5-10万'
        WHEN price < 15  THEN '10-15万'
        WHEN price < 20  THEN '15-20万'
        WHEN price < 30  THEN '20-30万'
        WHEN price < 50  THEN '30-50万'
        WHEN price < 100 THEN '50-100万'
        ELSE '100万以上'
    END                                  AS price_level,
    -- 折旧率 = 售价 / 新车指导价
    CASE
        WHEN original_price > 0 THEN ROUND(price / original_price, 4)
        ELSE NULL
    END                                  AS depreciation_rate
FROM used_car.ods_car_info
WHERE
    -- 过滤异常数据
    car_id IS NOT NULL
    AND brand IS NOT NULL AND TRIM(brand) != '' AND TRIM(brand) != 'nan'
    AND price IS NOT NULL AND price >= 0.5 AND price <= 500
    AND age IS NOT NULL AND age >= 0 AND age <= 30
    AND mileage IS NOT NULL AND mileage >= 0 AND mileage <= 50
;

-- ============================================================
-- 第二步：品牌价格汇总
-- ============================================================
INSERT OVERWRITE TABLE used_car.ads_brand_price
SELECT
    brand,
    COUNT(*)                              AS car_count,
    ROUND(AVG(price), 2)                  AS avg_price,
    ROUND(MIN(price), 2)                  AS min_price,
    ROUND(MAX(price), 2)                  AS max_price,
    ROUND(STDDEV(price), 2)               AS std_price
FROM used_car.dwd_car_info
WHERE dt='${hivevar:dt}'
GROUP BY brand
ORDER BY avg_price DESC
;

-- ============================================================
-- 第三步：车龄价格汇总
-- ============================================================
INSERT OVERWRITE TABLE used_car.ads_age_price
SELECT
    age,
    COUNT(*)                              AS car_count,
    ROUND(AVG(price), 2)                  AS avg_price,
    ROUND(AVG(mileage), 2)                AS avg_mileage
FROM used_car.dwd_car_info
WHERE dt='${hivevar:dt}'
GROUP BY age
ORDER BY age
;

-- ============================================================
-- 第四步：价格分布统计
-- ============================================================
INSERT OVERWRITE TABLE used_car.ads_price_distribution
SELECT
    price_level,
    COUNT(*)                              AS car_count,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 4) AS ratio
FROM used_car.dwd_car_info
WHERE dt='${hivevar:dt}'
GROUP BY price_level
ORDER BY
    CASE price_level
        WHEN '0-5万' THEN 1
        WHEN '5-10万' THEN 2
        WHEN '10-15万' THEN 3
        WHEN '15-20万' THEN 4
        WHEN '20-30万' THEN 5
        WHEN '30-50万' THEN 6
        WHEN '50-100万' THEN 7
        ELSE 8
    END
;

-- ============================================================
-- 验证输出
-- ============================================================
SELECT '=== DWD 清洗后数据量 ===' AS info;
SELECT COUNT(*) FROM used_car.dwd_car_info WHERE dt='${hivevar:dt}';

SELECT '=== 品牌价格 Top 10 ===' AS info;
SELECT * FROM used_car.ads_brand_price LIMIT 10;

SELECT '=== 车龄价格统计 ===' AS info;
SELECT * FROM used_car.ads_age_price;

SELECT '=== 价格分布 ===' AS info;
SELECT * FROM used_car.ads_price_distribution;
