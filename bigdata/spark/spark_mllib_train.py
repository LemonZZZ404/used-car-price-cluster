#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spark MLlib 随机森林回归模型训练
功能：
1. 从Hive读取清洗后数据
2. 特征工程：StringIndexer + OneHotEncoder + VectorAssembler
3. 训练随机森林回归模型预测二手车价格
4. 模型评估：RMSE, MAE, R2
5. 保存模型 + 特征重要性
用法：
  spark-submit --master yarn spark_mllib_train.py
  或本地运行（需配置SPARK_HOME）
"""

import os
import sys
import json
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import (
    StringIndexer, OneHotEncoder, VectorAssembler, StandardScaler
)
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# ============ 配置 ============
HIVE_DB = "used_car"
HIVE_TABLE = "dwd_car_info"
DT = "20240101"

MODEL_SAVE_PATH = "/tmp/spark_mllib_rf_model"
METRICS_SAVE_PATH = "/tmp/spark_mllib_metrics.json"

# 特征列定义
CATEGORICAL_COLS = ["brand", "gearbox", "fuel_type", "displacement", "city"]
NUMERIC_COLS = ["age", "mileage", "original_price"]
LABEL_COL = "price"


def create_spark():
    spark = (SparkSession.builder
             .appName("UsedCarPricePrediction_MLlib")
             .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
             .config("spark.driver.memory", "2g")
             .config("spark.executor.memory", "2g")
             .config("spark.sql.shuffle.partitions", "10")
             .enableHiveSupport()
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    print(f"[INFO] SparkSession 创建成功，版本: {spark.version}")
    return spark


def load_data(spark):
    """加载并预处理数据"""
    print(f"[INFO] 从Hive加载数据: {HIVE_DB}.{HIVE_TABLE}")
    df = spark.sql(f"""
        SELECT brand, gearbox, fuel_type, displacement, city,
               age, mileage, original_price, price
        FROM {HIVE_DB}.{HIVE_TABLE}
        WHERE dt = '{DT}'
          AND price IS NOT NULL AND price > 0
          AND age IS NOT NULL
          AND mileage IS NOT NULL
    """)

    # 填充缺失值
    df = df.na.fill({
        "brand": "未知", "gearbox": "自动", "fuel_type": "汽油",
        "displacement": "2.0L", "city": "未知",
        "original_price": 15.0
    })

    print(f"[INFO] 数据加载完成，共 {df.count()} 条")
    df.printSchema()
    return df


def build_pipeline():
    """构建特征工程 + 模型 Pipeline"""
    print("[INFO] 构建特征工程 Pipeline...")

    # 类别特征：StringIndexer + OneHotEncoder
    indexers = [
        StringIndexer(inputCol=col, outputCol=f"{col}_idx",
                      handleInvalid="keep")
        for col in CATEGORICAL_COLS
    ]
    encoders = [
        OneHotEncoder(inputCol=f"{col}_idx", outputCol=f"{col}_vec")
        for col in CATEGORICAL_COLS
    ]

    # 数值特征直接使用
    assembler_inputs = [f"{col}_vec" for col in CATEGORICAL_COLS] + NUMERIC_COLS
    assembler = VectorAssembler(
        inputCols=assembler_inputs,
        outputCol="features",
        handleInvalid="skip"
    )

    # 随机森林回归
    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol=LABEL_COL,
        predictionCol="prediction",
        numTrees=100,
        maxDepth=15,
        maxBins=64,
        minInstancesPerNode=5,
        featureSubsetStrategy="sqrt",
        seed=42
    )

    pipeline = Pipeline(stages=indexers + encoders + [assembler, rf])
    print("[INFO] Pipeline 构建完成")
    return pipeline


def train_and_evaluate(pipeline, train_df, test_df):
    """训练模型并评估"""
    print("\n" + "="*60)
    print("[训练] 开始训练随机森林回归模型...")
    print("="*60)

    model = pipeline.fit(train_df)
    print("[INFO] 模型训练完成")

    # 预测
    predictions = model.transform(test_df)
    predictions.select("price", "prediction", "brand", "age", "mileage").show(20, truncate=False)

    # 评估
    evaluator_rmse = RegressionEvaluator(
        labelCol=LABEL_COL, predictionCol="prediction", metricName="rmse")
    evaluator_mae = RegressionEvaluator(
        labelCol=LABEL_COL, predictionCol="prediction", metricName="mae")
    evaluator_r2 = RegressionEvaluator(
        labelCol=LABEL_COL, predictionCol="prediction", metricName="r2")

    rmse = evaluator_rmse.evaluate(predictions)
    mae = evaluator_mae.evaluate(predictions)
    r2 = evaluator_r2.evaluate(predictions)

    print("\n" + "="*60)
    print("[评估] 模型性能指标")
    print("="*60)
    print(f"  RMSE (均方根误差): {rmse:.4f} 万元")
    print(f"  MAE  (平均绝对误差): {mae:.4f} 万元")
    print(f"  R²   (决定系数):     {r2:.4f}")

    # 特征重要性
    rf_model = model.stages[-1]
    importances = rf_model.featureImportances
    print(f"\n[特征重要性] 特征向量维度: {len(importances)}")
    print(f"  Top 重要特征（前10）:")
    # 获取特征名
    feature_names = []
    for col in CATEGORICAL_COLS:
        feature_names.append(col)
    feature_names.extend(NUMERIC_COLS)

    importance_list = [(i, float(v)) for i, v in enumerate(importances.toArray())]
    importance_list.sort(key=lambda x: x[1], reverse=True)
    for idx, (i, imp) in enumerate(importance_list[:10]):
        print(f"    {idx+1}. 特征[{i}] 重要性 = {imp:.4f}")

    metrics = {
        "model": "Spark MLlib RandomForestRegressor",
        "train_size": train_df.count(),
        "test_size": test_df.count(),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "num_trees": rf_model.getNumTrees,
        "max_depth": rf_model.getMaxDepth(),
        "feature_importance_top10": [
            {"feature_index": i, "importance": round(imp, 4)}
            for i, imp in importance_list[:10]
        ],
        "train_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return model, metrics


def save_model(model, metrics):
    """保存模型和评估指标"""
    print("\n" + "="*60)
    print("[保存] 保存模型和评估指标")
    print("="*60)

    # 保存模型（覆盖）
    if os.path.exists(MODEL_SAVE_PATH):
        import shutil
        shutil.rmtree(MODEL_SAVE_PATH)
    model.save(MODEL_SAVE_PATH)
    print(f"  模型已保存至: {MODEL_SAVE_PATH}")

    # 保存指标
    with open(METRICS_SAVE_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  评估指标已保存至: {METRICS_SAVE_PATH}")

    # 同时保存到项目目录
    project_model_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ml', 'models')
    os.makedirs(project_model_dir, exist_ok=True)
    project_metrics_path = os.path.join(project_model_dir, 'spark_mllib_metrics.json')
    with open(project_metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  指标副本已保存至: {project_metrics_path}")


def main():
    print("="*60)
    print("二手车价格预测 - Spark MLlib 随机森林训练")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    spark = create_spark()

    try:
        # 1. 加载数据
        df = load_data(spark)

        # 2. 划分训练集/测试集 8:2（按brand分层抽样，避免训练集品牌单一触发OneHotEncoder报错）
        print("[INFO] 按品牌(brand)分层抽样划分训练/测试集 8:2...")
        df.cache()

        brands = [row["brand"] for row in df.select("brand").distinct().collect()]
        brand_cnt = len(brands)
        print(f"[INFO] 数据集品牌种类数: {brand_cnt}")
        if brand_cnt < 2:
            raise RuntimeError(
                f"[ERROR] 数据集品牌种类只有 {brand_cnt} 种，OneHotEncoder要求brand至少2种不同取值，"
                f"请检查原始数据是否只有单一品牌，或更换更大数据集。"
            )

        train_dfs, test_dfs = [], []
        for b in brands:
            sub_df = df.filter(F.col("brand") == b)
            sub_train, sub_test = sub_df.randomSplit([0.8, 0.2], seed=42)
            train_dfs.append(sub_train)
            test_dfs.append(sub_test)

        train_df = train_dfs[0]
        for d in train_dfs[1:]:
            train_df = train_df.unionByName(d)
        test_df = test_dfs[0]
        for d in test_dfs[1:]:
            test_df = test_df.unionByName(d)

        print(f"[INFO] 训练集: {train_df.count()} 条, 测试集: {test_df.count()} 条")
        print("[INFO] 训练集品牌分布:")
        train_df.groupBy("brand").count().orderBy(F.col("count").desc()).show(truncate=False)
        print("[INFO] 测试集品牌分布:")
        test_df.groupBy("brand").count().orderBy(F.col("count").desc()).show(truncate=False)

        # 3. 构建Pipeline
        pipeline = build_pipeline()

        # 4. 训练评估
        model, metrics = train_and_evaluate(pipeline, train_df, test_df)

        # 5. 保存
        save_model(model, metrics)

        print("\n" + "="*60)
        print("[ALL DONE] Spark MLlib 模型训练完成！")
        print(f"  RMSE: {metrics['rmse']} 万元")
        print(f"  MAE:  {metrics['mae']} 万元")
        print(f"  R²:   {metrics['r2']}")
        print("="*60)

    except Exception as e:
        print(f"[ERROR] 训练过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
