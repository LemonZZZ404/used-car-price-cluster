# 二手车价格评估系统设计与实现

> 基于大数据 + 机器学习的二手车价格评估系统，涵盖数据采集、存储、ETL、分析、建模、Web可视化全流程。

## 项目简介

本系统以二手车交易数据为基础，搭建完整的大数据处理链路，通过随机森林算法构建价格预测模型，并开发可视化Web系统，实现二手车智能估值和数据分析展示。

## 技术栈

### 大数据层
| 组件 | 版本 | 用途 |
|------|------|------|
| Hadoop | 3.3.4 | HDFS分布式存储 + YARN资源调度 |
| Hive | 3.1.3 | 数据仓库，ETL清洗，离线统计 |
| Sqoop | 1.4.7 | MySQL ↔ HDFS 数据导入导出 |
| Flume | 1.11.0 | 日志采集 |
| Spark | 3.3.2 | Spark SQL数据分析 + MLlib机器学习 |

### 数据存储
| 组件 | 用途 |
|------|------|
| MySQL | 业务数据、统计结果、预测记录 |
| Redis | 高频预测结果缓存 |
| HDFS | 原始数据、清洗后数据存储 |

### 机器学习
| 技术 | 用途 |
|------|------|
| Scikit-learn | 随机森林回归模型（Django在线预测用） |
| Spark MLlib | 分布式随机森林（离线训练对比） |

### Web层
| 技术 | 用途 |
|------|------|
| Django 4.2 + DRF | 后端RESTful API |
| Vue 3 + Vite | 前端框架 |
| Element Plus | UI组件库 |
| ECharts 5 | 数据可视化 |
| Nginx | 反向代理 + 静态文件服务 |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        数据采集层                              │
│   公开数据集CSV  │  Sqoop(MySQL→HDFS)  │  Flume(日志采集)   │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据存储层                              │
│         HDFS(原始/清洗数据)  │  MySQL(业务/统计)  │  Redis   │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      计算与分析层                              │
│    Hive ETL清洗  │  Spark SQL分析  │  Spark MLlib/sklearn建模 │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       应用层                                   │
│    Django + DRF (API接口 + 模型预测 + Redis缓存)             │
│    Vue3 + ECharts (数据看板 + 价格预测 + 车辆列表)           │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
used-car-price-system/
├── data/                    # 数据层
│   ├── dataset/             # 数据集（raw + clean）
│   ├── scripts/             # 数据预处理 + 模拟数据生成
│   └── sql/                 # MySQL建表脚本
├── bigdata/                 # 大数据层
│   ├── hive/                # Hive建表 + ETL
│   ├── sqoop/               # Sqoop导入脚本
│   ├── flume/               # Flume配置 + 日志生成
│   └── spark/               # Spark SQL分析 + MLlib训练
├── ml/                      # 机器学习层
│   ├── models/              # 训练好的模型 + 评估指标
│   ├── train_sklearn.py     # sklearn随机森林训练
│   └── compare_models.py    # 模型对比评估
├── backend/                 # Django后端
│   ├── config/              # Django项目配置
│   ├── car_api/             # API应用（models/views/serializers/services）
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Vue3前端
│   ├── src/
│   │   ├── views/           # 页面（Dashboard/Predict/CarList/History）
│   │   ├── api/             # API封装
│   │   ├── router/          # 路由
│   │   └── assets/          # 样式
│   ├── package.json
│   └── vite.config.js
├── deploy/                  # 部署
│   ├── DEPLOY.md            # 完整部署文档
│   ├── start_all.sh         # 一键启动
│   └── stop_all.sh          # 一键停止
└── docs/                    # 文档
```

## 快速开始

### 1. 环境要求
- JDK 1.8、Python 3.9+、Node.js 18+
- MySQL 8.0、Redis 6+
- Hadoop 3.3.x、Hive 3.1.x、Spark 3.3.x

### 2. 数据准备
```bash
# 生成模拟数据（无真实数据集时）
python3 data/scripts/generate_mock_data.py

# 数据预处理
python3 data/scripts/data_preprocess.py --mysql
```

### 3. 大数据流程
```bash
# Hive建表
hive -f bigdata/hive/create_tables.hql

# Hive ETL清洗
hive -f bigdata/hive/etl_clean.hql --hivevar dt=20240101

# Spark SQL分析（结果写入MySQL）
spark-submit --master local[*] bigdata/spark/spark_analysis.py

# Spark MLlib训练
spark-submit --master local[*] bigdata/spark/spark_mllib_train.py
```

### 4. 模型训练（sklearn，Django用）
```bash
pip3 install scikit-learn pandas numpy joblib
python3 ml/train_sklearn.py
```

### 5. 启动后端
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 修改配置
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 6. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 7. 访问
- 系统首页：http://localhost:5173
- 后端API：http://localhost:8000/api/health/
- 接口文档：http://localhost:8000/swagger/

## 核心功能

### 数据看板
- 车辆总数、品牌数、平均售价、预测次数统计卡片
- 品牌均价Top10柱状图
- 车龄-价格关系折线图
- 价格分布饼图
- 最近预测记录

### 价格预测
- 录入车辆参数（品牌、车龄、里程、变速箱、排量、燃油类型、城市、新车指导价）
- 随机森林模型预测二手车价格
- 展示预测价格、合理区间、置信度
- 支持sklearn和Spark MLlib两种模型切换

### 车辆列表
- 二手车数据分页展示
- 多条件筛选（品牌、价格区间、车龄区间、变速箱、燃油类型）
- 排序功能

### 预测历史
- 历史预测记录查询
- 模型类型标识

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health/` | GET | 健康检查 |
| `/api/dashboard/summary/` | GET | 看板概览 |
| `/api/cars/` | GET | 车辆列表 |
| `/api/cars/brands/` | GET | 品牌列表 |
| `/api/stat/brand-price/top10/` | GET | 品牌均价Top10 |
| `/api/stat/age-price/chart/` | GET | 车龄价格图表 |
| `/api/stat/price-distribution/chart/` | GET | 价格分布图表 |
| `/api/prediction/predict/` | POST | 价格预测 |
| `/api/prediction/history/` | GET | 预测历史 |

## 部署

详细部署步骤请参考 [deploy/DEPLOY.md](deploy/DEPLOY.md)，包含：
- 虚拟机环境搭建（JDK/Python/Node）
- MySQL/Redis安装配置
- Hadoop伪分布式部署
- Hive/Sqoop/Flume/Spark部署
- 数据导入与ETL流程
- Django后端部署
- Vue3前端部署
- Nginx反向代理
- 常见问题排查

## 作者

- 姓名：刘明哲
- 专业：大数据
- 项目：二手车价格评估系统设计与实现

## License

MIT
