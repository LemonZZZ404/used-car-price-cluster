#!/bin/bash
# ============================================================
# Sqoop 数据导入脚本（已修复列错位问题）
# 功能：将 MySQL 中的 car_info 表数据导入到 HDFS / Hive
# 用法：bash sqoop_import.sh
# 修复说明：
#   1) 增加 --columns 明确指定14列，跳过 Django 自增 id 主键，
#      避免 Hive ODS 表列错位导致 price/age 等数值列读为 NULL
#   2) 去掉 --direct，JDBC 模式对 --columns 支持更稳定
# ============================================================

MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASSWORD="123456"
MYSQL_DB="used_car"
MYSQL_TABLE="car_info"

HDFS_TARGET="/user/hive/warehouse/used_car/ods/ods_car_info"

echo "=========================================="
echo "Sqoop 导入: MySQL -> HDFS/Hive"
echo "表: ${MYSQL_DB}.${MYSQL_TABLE}"
echo "=========================================="

which sqoop > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[ERROR] 未找到 sqoop 命令，请先安装并配置环境变量"
    exit 1
fi

echo "[INFO] 开始导入数据到 HDFS: ${HDFS_TARGET}"
sqoop import \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useUnicode=true&characterEncoding=utf-8&useSSL=false" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASSWORD}" \
    --table "${MYSQL_TABLE}" \
    --columns "car_id,brand,series,model,price,original_price,age,mileage,gearbox,displacement,fuel_type,color,city,register_date" \
    --target-dir "${HDFS_TARGET}" \
    --delete-target-dir \
    --fields-terminated-by ',' \
    --lines-terminated-by '\n' \
    --null-string '\\N' \
    --null-non-string '\\N' \
    --m 1

if [ $? -eq 0 ]; then
    echo "[SUCCESS] 数据导入HDFS成功"
else
    echo "[ERROR] 数据导入HDFS失败，请检查连接和权限"
    exit 1
fi

echo "[INFO] HDFS 目标目录内容:"
hdfs dfs -ls -h "${HDFS_TARGET}"
echo "[INFO] 数据行数:"
hdfs dfs -cat "${HDFS_TARGET}/part-m-00000" 2>/dev/null | wc -l

echo ""
echo "=========================================="
echo "Sqoop 导入完成！"
echo "下一步：执行 Hive ETL 清洗"
echo "  hive -f bigdata/hive/etl_clean.hql --hivevar dt=20240101"
echo "=========================================="
