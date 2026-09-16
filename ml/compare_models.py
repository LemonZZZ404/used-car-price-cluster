#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型对比评估脚本
对比 Scikit-learn 随机森林 vs Spark MLlib 随机森林
输出对比表格，供论文使用
"""

import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKLEARN_METRICS = os.path.join(BASE_DIR, 'models', 'sklearn_metrics.json')
SPARK_METRICS = os.path.join(BASE_DIR, 'models', 'spark_mllib_metrics.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'models', 'model_comparison.md')


def load_metrics(path, name):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[INFO] 加载 {name} 指标成功")
        return data
    else:
        print(f"[WARN] 未找到 {name} 指标文件: {path}")
        return None


def main():
    print("="*60)
    print("模型对比评估: Scikit-learn vs Spark MLlib")
    print("="*60)

    sklearn_m = load_metrics(SKLEARN_METRICS, "Scikit-learn")
    spark_m = load_metrics(SPARK_METRICS, "Spark MLlib")

    # 构建对比表
    rows = []
    metrics_keys = [
        ("rmse", "RMSE (万元)", "均方根误差，越小越好"),
        ("mae", "MAE (万元)", "平均绝对误差，越小越好"),
        ("r2", "R² (决定系数)", "越接近1越好"),
    ]

    comparison_data = []
    for key, label, desc in metrics_keys:
        row = {"指标": label, "说明": desc}
        if sklearn_m:
            row["Scikit-learn"] = sklearn_m.get(key, "-")
        if spark_m:
            row["Spark MLlib"] = spark_m.get(key, "-")
        comparison_data.append(row)

    # 模型配置对比
    config_data = []
    config_keys = [
        ("model", "模型类型"),
        ("train_size", "训练集大小"),
        ("test_size", "测试集大小"),
        ("n_estimators", "树数量(numTrees)"),
        ("max_depth", "最大深度"),
        ("train_time", "训练时间"),
    ]
    for key, label in config_keys:
        row = {"配置项": label}
        if sklearn_m:
            row["Scikit-learn"] = sklearn_m.get(key, "-")
        if spark_m:
            row["Spark MLlib"] = spark_m.get(key, "-")
        config_data.append(row)

    # 生成Markdown报告
    md = []
    md.append("# 二手车价格预测模型对比评估报告\n")
    md.append("## 一、模型性能对比\n")
    md.append("| 指标 | 说明 | Scikit-learn 随机森林 | Spark MLlib 随机森林 |")
    md.append("|------|------|----------------------|---------------------|")
    for row in comparison_data:
        sk = row.get("Scikit-learn", "-")
        sp = row.get("Spark MLlib", "-")
        md.append(f"| {row['指标']} | {row['说明']} | {sk} | {sp} |")

    md.append("\n## 二、模型配置对比\n")
    md.append("| 配置项 | Scikit-learn | Spark MLlib |")
    md.append("|--------|-------------|-------------|")
    for row in config_data:
        sk = row.get("Scikit-learn", "-")
        sp = row.get("Spark MLlib", "-")
        md.append(f"| {row['配置项']} | {sk} | {sp} |")

    md.append("\n## 三、分析结论\n")
    md.append("### 3.1 精度对比\n")
    if sklearn_m and spark_m:
        sk_rmse = sklearn_m.get('rmse', 0)
        sp_rmse = spark_m.get('rmse', 0)
        if sk_rmse < sp_rmse:
            md.append(f"- Scikit-learn 模型 RMSE ({sk_rmse}) 略低于 Spark MLlib ({sp_rmse})，单机训练在小数据集上精度稍优。")
        else:
            md.append(f"- Spark MLlib 模型 RMSE ({sp_rmse}) 略低于 Scikit-learn ({sk_rmse})，分布式训练在特征处理上表现更好。")
        md.append(f"- 两者 R² 均在 {min(sklearn_m.get('r2',0), spark_m.get('r2',0)):.2f} 以上，模型拟合效果良好。")
    md.append("")
    md.append("### 3.2 适用场景\n")
    md.append("- **Scikit-learn**：适合单机、中小规模数据集，训练速度快，模型部署简单，适合Web系统在线预测。")
    md.append("- **Spark MLlib**：适合大规模、分布式数据集，可水平扩展，适合大数据场景下的离线批量训练。")
    md.append("- 本系统采用 **Scikit-learn 模型进行在线预测**（Django后端加载joblib模型），**Spark MLlib 用于离线训练和对比实验**，兼顾部署便捷性和大数据技术展示。")
    md.append("")
    md.append("### 3.3 改进方向\n")
    md.append("1. 尝试 XGBoost / LightGBM 等梯度提升模型，进一步提升预测精度；")
    md.append("2. 增加更多特征（车辆配置、事故记录、保养记录等）；")
    md.append("3. 对不同品牌分别建模，减少品牌间价格差异的影响；")
    md.append("4. 引入时间序列因素，考虑市场行情波动对价格的影响。")

    md_text = "\n".join(md)

    # 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(md_text)

    print(f"\n[DONE] 对比报告已保存: {OUTPUT_FILE}")
    print("\n" + md_text)


if __name__ == '__main__':
    main()
