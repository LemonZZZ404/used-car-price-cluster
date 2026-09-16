#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spark SQL 二手车数据分析脚本
功能：
1. 读取Hive清洗后的数据
2. 分析品牌-价格、车龄-价格、里程-价格关系
3. 统计价格分布
4. 结果写入MySQL，供前端ECharts展示
用法：
  spark-submit --master yarn --deploy-mode client spark_analysis.py
  或本地：python spark_analysis.py（需配置SPARK_HOME）
"""

import os
import sys
from datetime import datetime

# PySpark
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window

# ============ 配置 ============
HIVE_DB = "used_car"
HIVE_TABLE = "dwd_car_info"
DT = "20240101"  # 数据分区日期，根据实际修改

# MySQL配置（环境变量可覆盖，兼容单机/集群）
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DB = os.getenv("MYSQL_DB", "used_car")
MYSQL_URL = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?useUnicode=true&characterEncoding=utf-8&useSSL=false"
MYSQL_PROPERTIES = {
    "user": MYSQL_USER,
    "password": MYSQL_PASSWORD,
    "driver": "com.mysql.cj.jdbc.Driver"
}

# 输出目录
OUTPUT_DIR = "/tmp/spark_analysis_output"


def truncate_mysql_table(table_name):
    """
    【备用函数】已由 Spark 原生 .option("truncate","true") 替代，当前脚本不再调用。
    原作用：清空MySQL目标表（保留表结构，避免overwrite删表重建导致Django模型字段丢失）
    需要先执行 init_mysql.sql 建好表结构
    """
    try:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_URL.split("//")[1].split(":")[0],
            port=int(MYSQL_URL.split(":")[-1].split("/")[0]),
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            database=MYSQL_URL.split("/")[-1].split("?")[0],
            charset="utf8mb4"
        )
        with conn.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name}")
        conn.commit()
        conn.close()
        print(f"[INFO] 已清空MySQL表: {table_name}")
    except Exception as e:
        print(f"[WARN] 清空MySQL表 {table_name} 失败: {e}，继续使用append方式写入")


def create_spark():
    """创建SparkSession，集成Hive"""
    spark = (SparkSession.builder
             .appName("UsedCarPriceAnalysis")
             .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
             .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "512m"))
             .config("spark.executor.memory", os.getenv("SPARK_EXECUTOR_MEMORY", "512m"))
             .config("spark.sql.shuffle.partitions", "10")
             .enableHiveSupport()
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    print(f"[INFO] SparkSession 创建成功，版本: {spark.version}")
    return spark


def load_data(spark):
    """从Hive加载清洗后的数据"""
    print(f"[INFO] 从Hive加载数据: {HIVE_DB}.{HIVE_TABLE} dt={DT}")
    df = spark.sql(f"""
        SELECT car_id, brand, series, model, price, original_price,
               age, mileage, gearbox, displacement, fuel_type,
               color, city, register_date, price_level, depreciation_rate
        FROM {HIVE_DB}.{HIVE_TABLE}
        WHERE dt = '{DT}'
    """)
    print(f"[INFO] 数据加载完成，共 {df.count()} 条")
    df.printSchema()
    return df


def analyze_brand_price(df, spark):
    """分析品牌与价格关系"""
    print("\n" + "="*60)
    print("[分析] 品牌-价格统计")
    print("="*60)

    brand_df = df.groupBy("brand").agg(
        F.count("*").alias("car_count"),
        F.round(F.avg("price"), 2).alias("avg_price"),
        F.round(F.min("price"), 2).alias("min_price"),
        F.round(F.max("price"), 2).alias("max_price"),
        F.round(F.stddev("price"), 2).alias("std_price"),
        F.round(F.avg("age"), 1).alias("avg_age"),
        F.round(F.avg("mileage"), 2).alias("avg_mileage")
    ).orderBy(F.desc("avg_price"))

    brand_df.show(20, truncate=False)

    # 写入MySQL（Spark原生truncate：先清空表再整表写入，保留表结构/索引，Django模型字段不受影响）
    print("[INFO] 写入MySQL: stat_brand_price")
    brand_df.select(
        F.col("brand"),
        F.col("car_count").cast(LongType()),
        F.col("avg_price").cast(DecimalType(12, 2)),
        F.col("min_price").cast(DecimalType(12, 2)),
        F.col("max_price").cast(DecimalType(12, 2))
    ).write.mode("overwrite").option("truncate", "true").jdbc(
        url=MYSQL_URL,
        table="stat_brand_price",
        properties=MYSQL_PROPERTIES
    )
    print("[SUCCESS] 品牌价格统计已写入MySQL")
    return brand_df


def analyze_age_price(df, spark):
    """分析车龄与价格关系"""
    print("\n" + "="*60)
    print("[分析] 车龄-价格统计")
    print("="*60)

    age_df = df.groupBy("age").agg(
        F.count("*").alias("car_count"),
        F.round(F.avg("price"), 2).alias("avg_price"),
        F.round(F.avg("mileage"), 2).alias("avg_mileage"),
        F.round(F.avg("depreciation_rate"), 4).alias("avg_depreciation")
    ).orderBy("age")

    age_df.show(30, truncate=False)

    # 写入MySQL（Spark原生truncate：先清空表再整表写入，保留表结构/索引）
    print("[INFO] 写入MySQL: stat_age_price")
    age_df.select(
        F.col("age").cast(IntegerType()),
        F.col("car_count").cast(LongType()),
        F.col("avg_price").cast(DecimalType(12, 2))
    ).write.mode("overwrite").option("truncate", "true").jdbc(
        url=MYSQL_URL,
        table="stat_age_price",
        properties=MYSQL_PROPERTIES
    )
    print("[SUCCESS] 车龄价格统计已写入MySQL")
    return age_df


def analyze_price_distribution(df, spark):
    """统计价格分布"""
    print("\n" + "="*60)
    print("[分析] 价格分布统计")
    print("="*60)

    total = df.count()
    dist_df = df.groupBy("price_level").agg(
        F.count("*").alias("car_count"),
        F.round(F.count("*") / total * 100, 2).alias("percentage")
    ).orderBy(
        F.when(F.col("price_level") == "0-5万", 1)
        .when(F.col("price_level") == "5-10万", 2)
        .when(F.col("price_level") == "10-15万", 3)
        .when(F.col("price_level") == "15-20万", 4)
        .when(F.col("price_level") == "20-30万", 5)
        .when(F.col("price_level") == "30-50万", 6)
        .when(F.col("price_level") == "50-100万", 7)
        .otherwise(8)
    )

    dist_df.show(truncate=False)

    # 写入MySQL（Spark原生truncate：先清空表再整表写入，保留表结构/索引）
    print("[INFO] 写入MySQL: stat_price_distribution")
    dist_df.select(
        F.col("price_level").alias("price_range"),
        F.col("car_count").cast(LongType())
    ).write.mode("overwrite").option("truncate", "true").jdbc(
        url=MYSQL_URL,
        table="stat_price_distribution",
        properties=MYSQL_PROPERTIES
    )
    print("[SUCCESS] 价格分布统计已写入MySQL")
    return dist_df


def analyze_correlation(df, spark):
    """分析价格与各特征的相关性"""
    print("\n" + "="*60)
    print("[分析] 价格与特征相关性")
    print("="*60)

    # 数值特征相关性
    numeric_cols = ["price", "age", "mileage", "original_price", "depreciation_rate"]
    for col in numeric_cols[1:]:
        corr = df.stat.corr("price", col)
        print(f"  价格 vs {col}: 相关系数 = {corr:.4f}")

    # 变速箱对价格影响
    print("\n  变速箱-价格:")
    df.groupBy("gearbox").agg(
        F.round(F.avg("price"), 2).alias("avg_price"),
        F.count("*").alias("count")
    ).show()

    # 燃油类型对价格影响
    print("\n  燃油类型-价格:")
    df.groupBy("fuel_type").agg(
        F.round(F.avg("price"), 2).alias("avg_price"),
        F.count("*").alias("count")
    ).show()

    # 城市Top10均价
    print("\n  城市均价 Top 10:")
    df.groupBy("city").agg(
        F.round(F.avg("price"), 2).alias("avg_price"),
        F.count("*").alias("count")
    ).orderBy(F.desc("avg_price")).show(10)


def save_summary(brand_df, age_df, dist_df):
    """保存分析摘要到本地文件，供论文使用"""
    print("\n" + "="*60)
    print("[输出] 保存分析摘要")
    print("="*60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 品牌价格Top20
    brand_pd = brand_df.limit(20).toPandas()
    brand_pd.to_csv(f"{OUTPUT_DIR}/brand_price_top20_{timestamp}.csv",
                     index=False, encoding="utf-8-sig")
    print(f"  品牌价格Top20 -> {OUTPUT_DIR}/brand_price_top20_{timestamp}.csv")

    # 车龄价格
    age_pd = age_df.toPandas()
    age_pd.to_csv(f"{OUTPUT_DIR}/age_price_{timestamp}.csv",
                  index=False, encoding="utf-8-sig")
    print(f"  车龄价格 -> {OUTPUT_DIR}/age_price_{timestamp}.csv")

    # 价格分布
    dist_pd = dist_df.toPandas()
    dist_pd.to_csv(f"{OUTPUT_DIR}/price_distribution_{timestamp}.csv",
                    index=False, encoding="utf-8-sig")
    print(f"  价格分布 -> {OUTPUT_DIR}/price_distribution_{timestamp}.csv")

    print(f"\n[DONE] 分析摘要已保存至 {OUTPUT_DIR}")


def main():
    print("="*60)
    print("二手车价格评估系统 - Spark SQL 数据分析")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    spark = create_spark()

    try:
        # 1. 加载数据
        df = load_data(spark)
        df.cache()

        # 2. 品牌-价格分析
        brand_df = analyze_brand_price(df, spark)

        # 3. 车龄-价格分析
        age_df = analyze_age_price(df, spark)

        # 4. 价格分布
        dist_df = analyze_price_distribution(df, spark)

        # 5. 相关性分析
        analyze_correlation(df, spark)

        # 6. 保存摘要
        save_summary(brand_df, age_df, dist_df)

        print("\n" + "="*60)
        print("[ALL DONE] Spark SQL 数据分析全部完成！")
        print("结果已写入MySQL，前端可直接读取展示")
        print("="*60)

    except Exception as e:
        print(f"[ERROR] 分析过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()
        print("[INFO] SparkSession 已关闭")


if __name__ == "__main__":
    main()
