#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二手车数据预处理脚本
功能：
1. 读取原始CSV数据
2. 清洗：缺失值填充、异常值过滤、字段标准化
3. 输出清洗后CSV，供Hive/Spark使用
4. 可选：直接导入MySQL
"""

import pandas as pd
import numpy as np
import os
import sys
import argparse
from datetime import datetime

# 配置
RAW_FILE = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'raw_car_data.csv')
CLEAN_FILE = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'clean_car_data.csv')

# 品牌白名单（常见品牌）
BRAND_WHITELIST = [
    '大众', '丰田', '本田', '日产', '别克', '现代', '福特', '雪佛兰',
    '奥迪', '宝马', '奔驰', '雷克萨斯', '沃尔沃', '凯迪拉克', '林肯',
    '比亚迪', '吉利', '长安', '哈弗', '传祺', '奇瑞', '五菱', '宝骏',
    '特斯拉', '小鹏', '蔚来', '理想', '马自达', '斯巴鲁', '标致', '雪铁龙'
]

# 变速箱映射
GEARBOX_MAP = {
    '手动': '手动', 'MT': '手动', '手动挡': '手动',
    '自动': '自动', 'AT': '自动', '自动挡': '自动',
    'CVT': '自动', '双离合': '自动', 'DCT': '自动', 'AMT': '自动'
}

# 燃油类型映射
FUEL_MAP = {
    '汽油': '汽油', '燃油': '汽油', 'Gasoline': '汽油',
    '柴油': '柴油', 'Diesel': '柴油',
    '纯电动': '纯电动', '电动': '纯电动', 'EV': '纯电动', 'BEV': '纯电动',
    '混动': '混合动力', '混合动力': '混合动力', 'HEV': '混合动力', 'PHEV': '插电混动',
    '插电混动': '插电混动', '插电式混合动力': '插电混动'
}


def load_data(filepath):
    """加载原始数据，自动识别编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    for enc in encodings:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            print(f"[INFO] 使用编码 {enc} 读取成功，共 {len(df)} 行")
            return df
        except (UnicodeDecodeError, Exception):
            continue
    raise ValueError(f"无法读取文件 {filepath}，请检查编码格式")


def clean_data(df):
    """数据清洗主流程"""
    print(f"[INFO] 开始清洗，原始数据 {len(df)} 行，{len(df.columns)} 列")
    print(f"[INFO] 列名: {list(df.columns)}")

    # 统一列名为小写
    df.columns = [c.strip().lower() for c in df.columns]

    # 尝试识别关键列（兼容不同数据集字段名）
    col_map = {}
    for key, candidates in {
        'brand': ['brand', '品牌', 'car_brand'],
        'series': ['series', '车系', 'car_series'],
        'model': ['model', '车型', 'car_model', 'title'],
        'price': ['price', '售价', '价格', 'deal_price', 'sale_price'],
        'original_price': ['original_price', '新车价', '指导价', 'new_price'],
        'age': ['age', '车龄', 'car_age', 'years'],
        'mileage': ['mileage', '里程', '公里数', 'km', 'miles'],
        'gearbox': ['gearbox', '变速箱', 'transmission'],
        'displacement': ['displacement', '排量', 'engine'],
        'fuel_type': ['fuel_type', '燃油类型', '燃料', 'fuel'],
        'color': ['color', '颜色', '车身颜色'],
        'city': ['city', '城市', '所在城市', 'region'],
        'register_date': ['register_date', '上牌日期', '上牌时间', 'reg_date']
    }.items():
        for cand in candidates:
            if cand in df.columns:
                col_map[key] = cand
                break

    print(f"[INFO] 列映射: {col_map}")

    # 重命名列
    rename_dict = {v: k for k, v in col_map.items()}
    df = df.rename(columns=rename_dict)

    # 确保必要列存在
    required = ['brand', 'price', 'age', 'mileage']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[WARN] 缺少必要列: {missing}，将尝试用默认值填充")
        for c in missing:
            df[c] = np.nan

    # 补充缺失列
    for c in ['series', 'model', 'original_price', 'gearbox', 'displacement',
              'fuel_type', 'color', 'city', 'register_date']:
        if c not in df.columns:
            df[c] = np.nan

    # ---------- 价格清洗 ----------
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    # 过滤异常价格：0.5万 ~ 500万
    df = df[(df['price'] >= 0.5) & (df['price'] <= 500)]
    print(f"[INFO] 价格过滤后: {len(df)} 行")

    # ---------- 车龄清洗 ----------
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    # 如果车龄缺失但有上牌日期，计算车龄
    if 'register_date' in df.columns:
        df['register_date'] = pd.to_datetime(df['register_date'], errors='coerce')
        mask = df['age'].isna() & df['register_date'].notna()
        df.loc[mask, 'age'] = (datetime.now() - df.loc[mask, 'register_date']).dt.days / 365.25
    # 车龄范围：0 ~ 30年
    df = df[(df['age'] >= 0) & (df['age'] <= 30)]
    df['age'] = df['age'].round(0).astype(int)
    print(f"[INFO] 车龄清洗后: {len(df)} 行")

    # ---------- 里程清洗 ----------
    df['mileage'] = pd.to_numeric(df['mileage'], errors='coerce')
    # 里程范围：0 ~ 50万公里
    df = df[(df['mileage'] >= 0) & (df['mileage'] <= 50)]
    df['mileage'] = df['mileage'].round(2)
    print(f"[INFO] 里程清洗后: {len(df)} 行")

    # ---------- 品牌清洗 ----------
    df['brand'] = df['brand'].astype(str).str.strip()
    # 过滤空品牌
    df = df[df['brand'].notna() & (df['brand'] != '') & (df['brand'] != 'nan')]
    print(f"[INFO] 品牌清洗后: {len(df)} 行")

    # ---------- 变速箱标准化 ----------
    if 'gearbox' in df.columns:
        df['gearbox'] = df['gearbox'].astype(str).str.strip()
        df['gearbox'] = df['gearbox'].map(GEARBOX_MAP).fillna('自动')

    # ---------- 燃油类型标准化 ----------
    if 'fuel_type' in df.columns:
        df['fuel_type'] = df['fuel_type'].astype(str).str.strip()
        df['fuel_type'] = df['fuel_type'].map(FUEL_MAP).fillna('汽油')

    # ---------- 缺失值填充 ----------
    df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce')
    # 新车价缺失则用售价的1.5倍估算
    mask = df['original_price'].isna()
    df.loc[mask, 'original_price'] = (df.loc[mask, 'price'] * 1.5).round(2)

    df['series'] = df['series'].fillna('未知')
    df['model'] = df['model'].fillna('未知车型')
    df['displacement'] = df['displacement'].fillna('2.0L')
    df['color'] = df['color'].fillna('其他')
    df['city'] = df['city'].fillna('未知')

    # ---------- 去重 ----------
    before = len(df)
    df = df.drop_duplicates(subset=['brand', 'model', 'price', 'age', 'mileage', 'city'])
    print(f"[INFO] 去重: {before} -> {len(df)} 行")

    # 生成车辆唯一ID
    df['car_id'] = ['CAR' + str(i).zfill(8) for i in range(1, len(df) + 1)]

    # 选择输出列
    output_cols = ['car_id', 'brand', 'series', 'model', 'price', 'original_price',
                   'age', 'mileage', 'gearbox', 'displacement', 'fuel_type',
                   'color', 'city', 'register_date']
    output_cols = [c for c in output_cols if c in df.columns]
    df = df[output_cols]

    print(f"[INFO] 清洗完成，最终 {len(df)} 行，{len(df.columns)} 列")
    print(f"[INFO] 价格范围: {df['price'].min():.2f} ~ {df['price'].max():.2f} 万")
    print(f"[INFO] 车龄范围: {df['age'].min()} ~ {df['age'].max()} 年")
    print(f"[INFO] 品牌数量: {df['brand'].nunique()}")

    return df


def save_to_csv(df, filepath):
    """保存为CSV"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"[INFO] 已保存至: {filepath}")


def save_to_mysql(df, host='localhost', port=3306, user='root',
                  password='123456', database='used_car'):
    """导入MySQL（可选）"""
    try:
        from sqlalchemy import create_engine
        engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4')
        # 分批写入
        df.to_sql('car_info', engine, if_exists='append', index=False, chunksize=1000)
        print(f"[INFO] 已导入MySQL {database}.car_info，共 {len(df)} 条")
    except ImportError:
        print("[WARN] 未安装 sqlalchemy/pymysql，跳过MySQL导入")
    except Exception as e:
        print(f"[ERROR] MySQL导入失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='二手车数据预处理')
    parser.add_argument('--input', default=RAW_FILE, help='原始CSV路径')
    parser.add_argument('--output', default=CLEAN_FILE, help='清洗后CSV路径')
    parser.add_argument('--mysql', action='store_true', help='是否同时导入MySQL')
    parser.add_argument('--host', default='localhost', help='MySQL主机')
    parser.add_argument('--user', default='root', help='MySQL用户')
    parser.add_argument('--password', default='123456', help='MySQL密码')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] 输入文件不存在: {args.input}")
        print("[INFO] 请先将原始二手车数据集CSV放到 data/dataset/ 目录下")
        sys.exit(1)

    df = load_data(args.input)
    df_clean = clean_data(df)
    save_to_csv(df_clean, args.output)

    if args.mysql:
        save_to_mysql(df_clean, host=args.host, user=args.user, password=args.password)

    print("\n[DONE] 数据预处理完成！")


if __name__ == '__main__':
    main()
