#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟二手车数据生成脚本
如果没有真实数据集，可以用这个脚本生成模拟数据，保证整个流程能跑通。
生成约 20000 条模拟二手车数据。
"""

import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'raw_car_data.csv')

# 品牌及基础价格（万元）
BRANDS = {
    '大众': 15, '丰田': 16, '本田': 15, '日产': 14, '别克': 16,
    '现代': 12, '福特': 15, '雪佛兰': 13, '马自达': 14, '标致': 13,
    '奥迪': 35, '宝马': 38, '奔驰': 40, '雷克萨斯': 35, '沃尔沃': 32,
    '凯迪拉克': 30, '林肯': 33, '特斯拉': 28, '比亚迪': 14, '吉利': 10,
    '长安': 10, '哈弗': 11, '传祺': 12, '奇瑞': 9, '五菱': 6,
    '小鹏': 22, '蔚来': 35, '理想': 30
}

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
    '特斯拉': ['Model 3', 'Model Y', 'Model S', 'Model X']
}

GEARBOXES = ['手动', '自动']
DISPLACEMENTS = ['1.5L', '1.6L', '1.8L', '2.0L', '2.0T', '1.4T', '1.5T', '2.5L', '3.0T', '纯电']
FUEL_TYPES = ['汽油', '汽油', '汽油', '汽油', '柴油', '纯电动', '混合动力']
COLORS = ['白色', '黑色', '银色', '灰色', '红色', '蓝色', '棕色', '金色', '绿色']
CITIES = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆',
          '苏州', '天津', '长沙', '郑州', '青岛', '济南', '合肥', '福州', '厦门', '昆明']


def generate_car(index):
    """生成一条模拟二手车数据"""
    brand = random.choice(list(BRANDS.keys()))
    base_price = BRANDS[brand]

    # 车系
    if brand in SERIES_MAP:
        series = random.choice(SERIES_MAP[brand])
    else:
        series = random.choice(['标准版', '豪华版', '旗舰版', '运动版', '舒适版'])

    # 车龄：0-20年，偏向3-8年
    age = int(np.clip(np.random.gamma(2.5, 2.5), 0, 20))

    # 里程：与车龄正相关，年均1-2万公里
    mileage = round(age * np.random.uniform(0.8, 2.2) + np.random.uniform(0, 1), 2)
    mileage = min(mileage, 45)

    # 折旧率：车龄越大价格越低
    depreciation = 1.0
    if age <= 1:
        depreciation = np.random.uniform(0.75, 0.92)
    elif age <= 3:
        depreciation = np.random.uniform(0.55, 0.78)
    elif age <= 5:
        depreciation = np.random.uniform(0.40, 0.62)
    elif age <= 8:
        depreciation = np.random.uniform(0.28, 0.48)
    elif age <= 12:
        depreciation = np.random.uniform(0.18, 0.35)
    else:
        depreciation = np.random.uniform(0.08, 0.22)

    # 里程折旧
    mileage_factor = max(0.6, 1.0 - mileage * 0.015)

    # 随机波动
    random_factor = np.random.uniform(0.85, 1.15)

    price = round(base_price * depreciation * mileage_factor * random_factor, 2)
    price = max(price, 0.5)

    # 新车指导价
    original_price = round(base_price * np.random.uniform(0.95, 1.25), 2)

    gearbox = random.choice(GEARBOXES)
    displacement = random.choice(DISPLACEMENTS)
    fuel_type = random.choice(FUEL_TYPES)

    # 电动车特殊处理
    if brand in ['特斯拉', '小鹏', '蔚来', '理想'] or displacement == '纯电':
        fuel_type = '纯电动'
        gearbox = '自动'

    color = random.choice(COLORS)
    city = random.choice(CITIES)

    # 上牌日期
    register_date = (datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))).strftime('%Y-%m-%d')

    return {
        'car_id': f'CAR{index:08d}',
        'brand': brand,
        'series': series,
        'model': f'{brand} {series} {random.choice(["2018款", "2019款", "2020款", "2021款", "2022款"])} {displacement} {gearbox}',
        'price': price,
        'original_price': original_price,
        'age': age,
        'mileage': mileage,
        'gearbox': gearbox,
        'displacement': displacement,
        'fuel_type': fuel_type,
        'color': color,
        'city': city,
        'register_date': register_date
    }


def main():
    count = 20000
    print(f"[INFO] 正在生成 {count} 条模拟二手车数据...")

    data = [generate_car(i) for i in range(1, count + 1)]
    df = pd.DataFrame(data)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    print(f"[DONE] 已生成 {len(df)} 条数据，保存至: {OUTPUT_FILE}")
    print(f"\n数据概览:")
    print(f"  品牌数量: {df['brand'].nunique()}")
    print(f"  价格范围: {df['price'].min():.2f} ~ {df['price'].max():.2f} 万")
    print(f"  平均价格: {df['price'].mean():.2f} 万")
    print(f"  车龄范围: {df['age'].min()} ~ {df['age'].max()} 年")
    print(f"  里程范围: {df['mileage'].min():.2f} ~ {df['mileage'].max():.2f} 万公里")
    print(f"\n品牌分布 Top 10:")
    print(df['brand'].value_counts().head(10).to_string())


if __name__ == '__main__':
    main()
