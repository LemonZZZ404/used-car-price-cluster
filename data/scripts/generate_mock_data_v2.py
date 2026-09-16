#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大规模模拟二手车数据生成脚本（向量化，支持百万级）
输出：data/dataset/raw_car_data.csv（与 data_preprocess.py 完全兼容）
用法：python generate_mock_data_v2.py --count 1000000 [--output 自定义路径]

与原 generate_mock_data.py 的差异：
  1. 向量化生成（numpy/pandas），100 万条约几十秒，原脚本逐行循环会非常慢
  2. 品牌按市场份额加权抽样（大众/丰田/比亚迪多，豪车少），分布更真实
  3. 字段结构与清洗/训练脚本完全兼容
"""

import os
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dataset', 'raw_car_data.csv')

# 品牌及基础价格（万元）—— 与项目原脚本一致
BRANDS = {
    '大众': 15, '丰田': 16, '本田': 15, '日产': 14, '别克': 16,
    '现代': 12, '福特': 15, '雪佛兰': 13, '马自达': 14, '标致': 13,
    '奥迪': 35, '宝马': 38, '奔驰': 40, '雷克萨斯': 35, '沃尔沃': 32,
    '凯迪拉克': 30, '林肯': 33, '特斯拉': 28, '比亚迪': 14, '吉利': 10,
    '长安': 10, '哈弗': 11, '传祺': 12, '奇瑞': 9, '五菱': 6,
    '小鹏': 22, '蔚来': 35, '理想': 30
}

# 品牌市场份额权重（近似销量分布）
BRAND_WEIGHTS = {
    '大众': 0.10, '丰田': 0.09, '本田': 0.08, '比亚迪': 0.10, '吉利': 0.08,
    '长安': 0.07, '日产': 0.06, '五菱': 0.05, '别克': 0.05, '哈弗': 0.04,
    '现代': 0.04, '奥迪': 0.03, '宝马': 0.03, '奔驰': 0.03, '福特': 0.03,
    '雪佛兰': 0.03, '传祺': 0.02, '特斯拉': 0.02, '奇瑞': 0.02, '马自达': 0.02,
    '小鹏': 0.01, '蔚来': 0.01, '理想': 0.01, '标致': 0.01, '雷克萨斯': 0.01,
    '沃尔沃': 0.01, '凯迪拉克': 0.01, '林肯': 0.005
}
_bw = np.array([BRAND_WEIGHTS[b] for b in BRANDS])
BRAND_WEIGHTS_NORM = _bw / _bw.sum()

SERIES_MAP = {
    '大众': ['朗逸', '速腾', '迈腾', '帕萨特', '途观', '高尔夫', '宝来', '途昂'],
    '丰田': ['卡罗拉', '凯美瑞', '雷凌', 'RAV4', '汉兰达', '普拉多', '亚洲龙', '威驰'],
    '本田': ['思域', '雅阁', 'CR-V', '飞度', '缤智', 'XR-V', '皓影', '冠道'],
    '日产': ['轩逸', '天籁', '奇骏', '逍客', '骐达', '楼兰', '蓝鸟', '劲客'],
    '别克': ['英朗', '君威', '君越', '昂科威', '威朗', 'GL8', '昂科拉', '凯越'],
    '现代': ['伊兰特', '索纳塔', '途胜', 'ix35', '名图', '领动', '菲斯塔', '胜达'],
    '福特': ['福克斯', '蒙迪欧', '翼虎', '福睿斯', '锐界', '探险者', '金牛座', '嘉年华'],
    '雪佛兰': ['科鲁兹', '迈锐宝', '科沃兹', '探界者', '创酷', '赛欧', '沃兰多', '开拓者'],
    '奥迪': ['A4L', 'A6L', 'A3', 'Q5L', 'Q3', 'A8L', 'Q7', 'Q2L'],
    '宝马': ['3系', '5系', '1系', 'X3', 'X1', '7系', 'X5', '2系'],
    '奔驰': ['C级', 'E级', 'A级', 'GLC', 'GLA', 'S级', 'GLE', 'GLB'],
    '比亚迪': ['宋', '秦', '唐', '汉', '元', '海豚', '海豹', '驱逐舰05'],
    '吉利': ['帝豪', '博越', '星瑞', '缤越', '远景', '嘉际', '星越', '豪越'],
    '特斯拉': ['Model 3', 'Model Y', 'Model S', 'Model X'],
    '长安': ['CS75', '逸动', 'CS55', 'UNI-V', '锐程', 'CS35', 'UNI-K', '糯玉米'],
    '哈弗': ['H6', '大狗', 'M6', 'F7', '初恋', '赤兔', '神兽', '枭龙'],
    '传祺': ['GS4', 'GS8', '影豹', 'M8', 'GA6', '影酷', 'GS3', 'E9'],
    '奇瑞': ['瑞虎8', '艾瑞泽5', '瑞虎7', '瑞虎5x', '艾瑞泽8', '探索06', '捷途X70', 'QQ冰淇淋'],
    '五菱': ['宏光MINI', '宏光S', '星辰', '凯捷', '缤果', '星驰', '之光', '荣光'],
    '小鹏': ['P7', 'P5', 'G3', 'G6', 'G9', 'X9'],
    '蔚来': ['ES6', 'ES8', 'ET5', 'ET7', 'EC6', 'ES7'],
    '理想': ['L7', 'L8', 'L9', 'ONE'],
    '马自达': ['昂克赛拉', '阿特兹', 'CX-4', 'CX-5', 'CX-30', 'CX-8'],
    '标致': ['408', '508', '4008', '5008', '2008', '308'],
    '雷克萨斯': ['ES', 'RX', 'NX', 'UX', 'LS', 'LM'],
    '沃尔沃': ['S60', 'S90', 'XC40', 'XC60', 'XC90', 'V60'],
    '凯迪拉克': ['CT5', 'CT6', 'XT4', 'XT5', 'XT6', 'GT4'],
    '林肯': ['冒险家', '航海家', '飞行家', '领航员', 'Z']
}
FALLBACK_SERIES = ['标准版', '豪华版', '旗舰版', '运动版', '舒适版']

GEARBOXES = ['手动', '自动']
DISPLACEMENTS = ['1.5L', '1.6L', '1.8L', '2.0L', '2.0T', '1.4T', '1.5T', '2.5L', '3.0T', '纯电']
DISPLACEMENT_WEIGHTS = [0.15, 0.12, 0.10, 0.15, 0.10, 0.12, 0.15, 0.06, 0.02, 0.03]
FUEL_TYPES = ['汽油', '汽油', '汽油', '汽油', '柴油', '纯电动', '混合动力']
FUEL_WEIGHTS = [0.60, 0.06, 0.12, 0.08, 0.02, 0.08, 0.04]
COLORS = ['白色', '黑色', '银色', '灰色', '红色', '蓝色', '棕色', '金色', '绿色']
CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆',
          '苏州', '天津', '长沙', '郑州', '青岛', '济南', '合肥', '福州', '厦门', '昆明']
MODEL_YEARS = ['2018款', '2019款', '2020款', '2021款', '2022款']

EV_BRANDS = {'特斯拉', '小鹏', '蔚来', '理想'}


def generate(count, seed=42):
    """向量化生成 count 条二手车数据，返回 DataFrame"""
    rng = np.random.default_rng(seed)
    n = count

    # ---- 品牌（加权抽样）----
    brand_arr = rng.choice(list(BRANDS.keys()), size=n, p=BRAND_WEIGHTS_NORM)
    base_price_arr = np.array([BRANDS[b] for b in brand_arr], dtype=float)

    # ---- 车系（按品牌查表）----
    series_arr = np.array([
        rng.choice(SERIES_MAP.get(b, FALLBACK_SERIES)) for b in brand_arr
    ])

    # ---- 车龄：偏向 3-8 年，截断 0-20 ----
    age_arr = np.clip(rng.gamma(2.5, 2.5, n), 0, 20).astype(int)

    # ---- 里程：与车龄正相关，年均 0.8-2.2 万公里 ----
    mileage_arr = np.minimum(age_arr * rng.uniform(0.8, 2.2, n) + rng.uniform(0, 1, n), 45).round(2)

    # ---- 折旧率（按车龄分段）----
    depreciation = np.select(
        [age_arr <= 1, age_arr <= 3, age_arr <= 5, age_arr <= 8, age_arr <= 12],
        [rng.uniform(0.75, 0.92, n), rng.uniform(0.55, 0.78, n),
         rng.uniform(0.40, 0.62, n), rng.uniform(0.28, 0.48, n),
         rng.uniform(0.18, 0.35, n)],
        default=rng.uniform(0.08, 0.22, n)
    )

    # ---- 里程折旧 + 随机波动 ----
    mileage_factor = np.maximum(0.6, 1.0 - mileage_arr * 0.015)
    random_factor = rng.uniform(0.85, 1.15, n)

    price_arr = np.maximum(base_price_arr * depreciation * mileage_factor * random_factor, 0.5).round(2)
    original_price_arr = (base_price_arr * rng.uniform(0.95, 1.25, n)).round(2)

    # ---- 变速箱 / 排量 / 燃油 / 颜色 / 城市 ----
    gearbox_arr = rng.choice(GEARBOXES, size=n, p=[0.25, 0.75])
    displacement_arr = rng.choice(DISPLACEMENTS, size=n, p=DISPLACEMENT_WEIGHTS)
    fuel_arr = rng.choice(FUEL_TYPES, size=n, p=FUEL_WEIGHTS)
    color_arr = rng.choice(COLORS, size=n)
    city_arr = rng.choice(CITIES, size=n)

    # ---- 电动车特判：电动品牌或纯电排量 → 纯电动 + 自动 ----
    ev_mask = np.array([b in EV_BRANDS for b in brand_arr]) | (displacement_arr == '纯电')
    fuel_arr = fuel_arr.copy()
    gearbox_arr = gearbox_arr.copy()
    fuel_arr[ev_mask] = '纯电动'
    gearbox_arr[ev_mask] = '自动'

    # ---- model 字段 ----
    year_arr = rng.choice(MODEL_YEARS, size=n)
    model_arr = np.array([
        f"{b} {s} {y} {d} {g}"
        for b, s, y, d, g in zip(brand_arr, series_arr, year_arr, displacement_arr, gearbox_arr)
    ])

    # ---- 上牌日期 ----
    today = pd.Timestamp(datetime.now().date())
    days_ago = age_arr * 365 + rng.integers(0, 366, n)
    register_arr = (today - pd.to_timedelta(days_ago, unit='D')).strftime('%Y-%m-%d')

    # ---- 车辆 ID ----
    car_id_arr = np.array([f'CAR{i:08d}' for i in range(1, n + 1)])

    df = pd.DataFrame({
        'car_id': car_id_arr,
        'brand': brand_arr,
        'series': series_arr,
        'model': model_arr,
        'price': price_arr,
        'original_price': original_price_arr,
        'age': age_arr,
        'mileage': mileage_arr,
        'gearbox': gearbox_arr,
        'displacement': displacement_arr,
        'fuel_type': fuel_arr,
        'color': color_arr,
        'city': city_arr,
        'register_date': register_arr,
    })
    return df


def main():
    parser = argparse.ArgumentParser(description='大规模模拟二手车数据生成')
    parser.add_argument('--count', type=int, default=1000000, help='生成条数（默认 1000000）')
    parser.add_argument('--output', default=OUTPUT_FILE, help='输出 CSV 路径')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    args = parser.parse_args()

    print(f"[INFO] 开始生成 {args.count:,} 条模拟二手车数据（向量化）...")
    t0 = time.time()

    df = generate(args.count, seed=args.seed)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_csv(args.output, index=False, encoding='utf-8-sig')

    elapsed = time.time() - t0
    print(f"[DONE] 生成 {len(df):,} 条，耗时 {elapsed:.1f} 秒，保存至: {args.output}")
    print(f"文件大小: {os.path.getsize(args.output) / 1024 / 1024:.1f} MB")

    print(f"\n数据概览:")
    print(f"  品牌数量: {df['brand'].nunique()}")
    print(f"  价格范围: {df['price'].min():.2f} ~ {df['price'].max():.2f} 万")
    print(f"  平均价格: {df['price'].mean():.2f} 万")
    print(f"  车龄范围: {df['age'].min()} ~ {df['age'].max()} 年")
    print(f"  里程范围: {df['mileage'].min():.2f} ~ {df['mileage'].max():.2f} 万公里")
    print(f"  上牌日期: {df['register_date'].min()} ~ {df['register_date'].max()}")
    print(f"\n品牌分布 Top 10:")
    print(df['brand'].value_counts().head(10).to_string())
    print(f"\n燃油类型分布:")
    print(df['fuel_type'].value_counts().to_string())


if __name__ == '__main__':
    import time
    main()
