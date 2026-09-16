#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scikit-learn 随机森林回归模型训练
功能：
1. 读取清洗后CSV数据
2. 特征工程：类别编码 + 数值特征
3. 训练随机森林回归模型
4. 模型评估：RMSE, MAE, R2
5. 保存模型（joblib）供Django后端调用
6. 保存特征编码器，保证预测时特征一致
用法：python train_sklearn.py
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# ============ 配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, '..', 'data', 'dataset', 'clean_car_data.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
MODEL_FILE = os.path.join(MODEL_DIR, 'rf_price_model.joblib')
PREPROCESSOR_FILE = os.path.join(MODEL_DIR, 'preprocessor.joblib')
METRICS_FILE = os.path.join(MODEL_DIR, 'sklearn_metrics.json')
FEATURE_IMPORTANCE_FILE = os.path.join(MODEL_DIR, 'feature_importance.json')

# 特征定义
CATEGORICAL_COLS = ['brand', 'gearbox', 'fuel_type', 'displacement', 'city']
NUMERIC_COLS = ['age', 'mileage', 'original_price']
LABEL_COL = 'price'
ALL_FEATURES = CATEGORICAL_COLS + NUMERIC_COLS


def load_data():
    """加载清洗后数据"""
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] 数据文件不存在: {DATA_FILE}")
        print("[INFO] 请先运行数据预处理脚本生成清洗后数据")
        sys.exit(1)

    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    print(f"[INFO] 数据加载完成，共 {len(df)} 行，{len(df.columns)} 列")

    # 确保必要列存在
    for col in ALL_FEATURES + [LABEL_COL]:
        if col not in df.columns:
            print(f"[WARN] 缺少列: {col}，将用默认值填充")
            if col in NUMERIC_COLS:
                df[col] = df[col].median() if col in df.columns else 0
            else:
                df[col] = '未知'

    # 过滤异常
    df = df[(df[LABEL_COL] > 0) & (df[LABEL_COL] < 500)]
    df = df[df['age'].between(0, 30)]
    df = df[df['mileage'].between(0, 50)]

    print(f"[INFO] 过滤后数据: {len(df)} 行")
    return df


def build_preprocessor():
    """构建预处理Pipeline"""
    # 数值特征：中位数填充 + 标准化
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # 类别特征：众数填充 + LabelEncoder（用在ColumnTransformer里）
    # 注意：sklearn的OneHotEncoder可以直接处理字符串
    from sklearn.preprocessing import OneHotEncoder
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUMERIC_COLS),
            ('cat', categorical_transformer, CATEGORICAL_COLS)
        ],
        remainder='drop'
    )

    return preprocessor


def train_model(X_train, y_train):
    """训练随机森林模型（带网格搜索调参）"""
    print("\n" + "="*60)
    print("[训练] 随机森林回归模型")
    print("="*60)

    # 基础模型
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features='sqrt',
        n_jobs=-1,
        random_state=42,
        verbose=1
    )

    # 完整Pipeline：预处理 + 模型
    model = Pipeline(steps=[
        ('preprocessor', build_preprocessor()),
        ('regressor', rf)
    ])

    print("[INFO] 开始训练...")
    start_time = datetime.now()
    model.fit(X_train, y_train)
    train_time = (datetime.now() - start_time).total_seconds()
    print(f"[INFO] 训练完成，耗时: {train_time:.2f} 秒")

    return model, train_time


def evaluate_model(model, X_test, y_test, train_time=0.0):
    """模型评估"""
    print("\n" + "="*60)
    print("[评估] 模型性能")
    print("="*60)

    y_pred = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # 相对误差
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

    print(f"  RMSE (均方根误差):  {rmse:.4f} 万元")
    print(f"  MAE  (平均绝对误差): {mae:.4f} 万元")
    print(f"  MAPE (平均绝对百分比): {mape:.2f}%")
    print(f"  R²   (决定系数):      {r2:.4f}")

    # 预测样例
    print("\n  预测样例（前10条）:")
    sample = pd.DataFrame({
        '真实价格': y_test[:10].values,
        '预测价格': y_pred[:10].round(2),
        '误差': (y_test[:10].values - y_pred[:10]).round(2)
    })
    print(sample.to_string(index=False))

    metrics = {
        "model": "Scikit-learn RandomForestRegressor",
        "train_size": len(X_train),
        "test_size": len(X_test),
        "rmse": round(float(rmse), 4),
        "mae": round(float(mae), 4),
        "mape": round(float(mape), 2),
        "r2": round(float(r2), 4),
        "n_estimators": model.named_steps['regressor'].n_estimators,
        "max_depth": model.named_steps['regressor'].max_depth,
        "train_time_seconds": round(train_time, 2),
        "train_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return metrics, y_pred


def analyze_feature_importance(model, X_train):
    """分析特征重要性"""
    print("\n" + "="*60)
    print("[特征重要性]")
    print("="*60)

    regressor = model.named_steps['regressor']
    preprocessor = model.named_steps['preprocessor']

    # 获取特征名
    feature_names = []
    # 数值特征
    feature_names.extend(NUMERIC_COLS)
    # 类别特征onehot后的名字
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_COLS)
    feature_names.extend(cat_feature_names)

    importances = regressor.feature_importances_
    indices = np.argsort(importances)[::-1]

    print(f"  总特征数: {len(feature_names)}")
    print(f"  Top 15 重要特征:")
    top_features = []
    for f in range(min(15, len(feature_names))):
        idx = indices[f]
        print(f"    {f+1:2d}. {feature_names[idx]:40s} 重要性: {importances[idx]:.4f}")
        top_features.append({
            "feature": feature_names[idx],
            "importance": round(float(importances[idx]), 4)
        })

    return top_features


def save_model(model, metrics, feature_importance):
    """保存模型和指标"""
    print("\n" + "="*60)
    print("[保存] 模型文件")
    print("="*60)

    os.makedirs(MODEL_DIR, exist_ok=True)

    # 保存完整Pipeline（包含预处理）
    joblib.dump(model, MODEL_FILE)
    print(f"  模型已保存: {MODEL_FILE}")

    # 保存评估指标
    with open(METRICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  评估指标已保存: {METRICS_FILE}")

    # 保存特征重要性
    with open(FEATURE_IMPORTANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(feature_importance, f, ensure_ascii=False, indent=2)
    print(f"  特征重要性已保存: {FEATURE_IMPORTANCE_FILE}")

    # 模型文件大小
    model_size = os.path.getsize(MODEL_FILE) / 1024 / 1024
    print(f"  模型文件大小: {model_size:.2f} MB")


def quick_predict_test(model):
    """快速预测测试，验证模型可用"""
    print("\n" + "="*60)
    print("[验证] 快速预测测试")
    print("="*60)

    test_cases = [
        {"brand": "大众", "gearbox": "自动", "fuel_type": "汽油",
         "displacement": "1.4T", "city": "北京", "age": 3, "mileage": 4.5, "original_price": 16.0},
        {"brand": "宝马", "gearbox": "自动", "fuel_type": "汽油",
         "displacement": "2.0T", "city": "上海", "age": 2, "mileage": 3.0, "original_price": 38.0},
        {"brand": "比亚迪", "gearbox": "自动", "fuel_type": "纯电动",
         "displacement": "纯电", "city": "深圳", "age": 1, "mileage": 1.5, "original_price": 14.0},
    ]

    test_df = pd.DataFrame(test_cases)
    predictions = model.predict(test_df[ALL_FEATURES])

    for i, (case, pred) in enumerate(zip(test_cases, predictions)):
        print(f"  测试{i+1}: {case['brand']} | 车龄{case['age']}年 | 里程{case['mileage']}万 "
              f"-> 预测价格: {pred:.2f} 万元")


if __name__ == '__main__':
    print("="*60)
    print("二手车价格预测 - Scikit-learn 随机森林训练")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 1. 加载数据
    df = load_data()

    # 2. 划分特征和标签
    X = df[ALL_FEATURES]
    y = df[LABEL_COL]

    # 3. 划分训练集/测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"[INFO] 训练集: {len(X_train)} 条, 测试集: {len(X_test)} 条")

    # 4. 训练模型
    model, train_time = train_model(X_train, y_train)

    # 5. 评估
    metrics, y_pred = evaluate_model(model, X_test, y_test, train_time)

    # 6. 特征重要性
    feature_importance = analyze_feature_importance(model, X_train)

    # 7. 保存
    save_model(model, metrics, feature_importance)

    # 8. 快速预测验证
    quick_predict_test(model)

    print("\n" + "="*60)
    print("[ALL DONE] Scikit-learn 模型训练完成！")
    print(f"  RMSE: {metrics['rmse']} 万元")
    print(f"  MAE:  {metrics['mae']} 万元")
    print(f"  R²:   {metrics['r2']}")
    print(f"  模型文件: {MODEL_FILE}")
    print("="*60)
