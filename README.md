# 二手车价格评估系统设计与实现（三机集群版）

> 基于**三机 Hadoop 集群 + 机器学习**的二手车价格评估系统，覆盖数据采集、数仓分层、ETL、Spark 分析、建模、Web 可视化全流程。
> 本仓库为集群部署版，**100 万条数据全链路跑通**；集群部署细节见 [deploy/CLUSTER_DEPLOY.md](deploy/CLUSTER_DEPLOY.md)。

## 项目简介

以 1,000,000 条二手车交易数据为基础，在三机分布式集群上搭建完整大数据处理链路：Sqoop 采集入库 → Hive 数仓分层（ODS/DWD/ADS）→ Spark 分析回写 MySQL → Django 提供 RESTful API → Vue3 可视化展示；基于随机森林回归实现价格预测，并支持 SHAP 影响因子解释与 Celery 异步一键重训。

## 集群架构

| 主机 | IP | 组件 |
|------|-----|------|
| hadoop101 | 192.168.249.101 | NameNode / JobHistoryServer / Hive(Metastore+HS2) / MySQL / Redis / Django / Nginx / Celery / ZK / Kafka |
| hadoop102 | 192.168.249.102 | ResourceManager / DataNode / NodeManager / ZK / Kafka |
| hadoop103 | 192.168.249.103 | SecondaryNameNode / DataNode / NodeManager / ZK / Kafka |

## 技术栈

### 大数据层
| 组件 | 版本 | 用途 |
|------|------|------|
| Hadoop | 3.1.3 | HDFS 分布式存储 + YARN 资源调度 |
| Hive | 3.1.2 | 数据仓库（ODS/DWD/ADS 分层），ETL 清洗 |
| Spark | 3.0.0 | Spark SQL 数据分析 + MLlib 机器学习 |
| Sqoop | 1.4.6 | MySQL ↔ HDFS 数据导入 |
| Kafka | 2.4.1 | 日志消息队列（三节点） |
| Zookeeper | 3.5.7 | 集群协调（三节点） |
| Flume | - | 日志采集 |

### 数据存储
| 组件 | 用途 |
|------|------|
| MySQL | 业务数据（100 万条）、统计结果、预测记录 |
| Redis | 高频预测结果缓存 + Celery broker |
| HDFS | 原始数据、数仓分层数据存储 |

### 机器学习
| 技术 | 用途 |
|------|------|
| Scikit-learn | 随机森林回归（Django 在线预测，R²=0.9323） |
| Spark MLlib | 分布式随机森林（离线训练对比） |
| SHAP | 预测结果影响因子解释 |

### Web 层
| 技术 | 用途 |
|------|------|
| Django 4.2 + DRF | 后端 RESTful API |
| Vue 3 + Vite | 前端框架 |
| Element Plus | UI 组件库 |
| ECharts 5 | 数据可视化 |
| Nginx | 反向代理 + 静态文件服务 |
| Celery | 异步训练任务 |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        数据采集层                              │
│   MySQL car_info (100万条) ──Sqoop 14列精确导入──▶ HDFS ODS    │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    数仓分层（Hive, MR引擎）                    │
│        ODS ods_car_info (999,999) → DWD dwd_car_info          │
│                     (清洗后 999,998, dt=20240101)              │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    计算与分析层（Spark on YARN）               │
│    Spark SQL 聚合 → 写回 MySQL stat_brand/age/price 三表      │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       应用层（hadoop101）                     │
│    Django + DRF (API + 模型预测 + SHAP + Redis缓存)           │
│    Vue3 + ECharts (数据看板 + 价格预测 + 车辆列表) ← Nginx :80 │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
used-car-price-cluster/
├── data/                    # 数据层
│   ├── scripts/             # 数据预处理 + 模拟数据生成
│   └── sql/                 # MySQL 建表脚本
├── bigdata/                 # 大数据层
│   ├── hive/                # Hive 建表 + ETL 清洗（MR 引擎）
│   ├── sqoop/               # Sqoop 14 列导入脚本
│   ├── flume/               # Flume 配置 + 日志生成
│   └── spark/               # Spark SQL 分析 + MLlib 训练
├── ml/                      # 机器学习层
│   ├── train_sklearn.py     # 随机森林训练
│   └── compare_models.py    # 模型对比评估
├── backend/                 # Django 后端
│   ├── config/              # 项目配置（含 MariaDB 兼容 + Celery）
│   ├── car_api/             # API 应用（models/views/serializers/tasks）
│   ├── manage.py
│   └── requirements.txt
├── frontend/                # Vue3 前端
│   ├── src/views/           # Dashboard/Predict/CarList/History/ModelAnalysis
│   ├── src/api/             # API 封装
│   └── vite.config.js
└── deploy/                  # 集群部署
    ├── CLUSTER_DEPLOY.md    # ★ 集群部署文档（架构/链路/踩坑）
    ├── start_all.sh         # ★ 三机一键启动（幂等）
    └── stop_all.sh          # ★ 三机一键停止
```

## 快速开始（集群）

### 1. 环境要求
- JDK 1.8、Python 3.9+、Node.js 18+
- 三机集群：Hadoop 3.1.3 / Hive 3.1.2 / Spark 3.0.0 / MySQL / Redis，SSH 互信
- 数据：MySQL `car_info` 100 万条（`data/scripts/generate_mock_data.py` 生成）

### 2. 一键启动 / 停止（在 hadoop101 执行）
```bash
bash deploy/start_all.sh    # MySQL→Redis→ZK→HDFS/YARN→Kafka→Hive→Django→Nginx→Celery
bash deploy/stop_all.sh     # 反向停止（MySQL 默认保留）
```
访问：`http://192.168.249.101/`

### 3. 手工跑批（数据更新后）
```bash
# ① Sqoop 导入（14 列对齐）
bash bigdata/sqoop/sqoop_import.sh

# ② Hive ETL（MR 引擎）
beeline -u "jdbc:hive2://hadoop101:10000/default" -n gk -p gk --silent=true \
  -f bigdata/hive/etl_clean.hql --hivevar dt=20240101 --hiveconf hive.execution.engine=mr

# ③ Spark 分析写 MySQL stat_*（环境变量可覆盖主机/密码/内存）
cd bigdata/spark
MYSQL_PASSWORD='xxxx' \
spark-submit --master yarn --deploy-mode client \
  --jars /opt/module/spark/jars/mysql-connector-java-8.0.30.jar \
  spark_analysis.py
```

### 4. 模型训练（sklearn，Django 在线预测用）
```bash
python3 ml/train_sklearn.py      # 读 data/dataset/clean_car_data.csv
```
训练结果：RandomForest，R²=0.9323，RMSE=1.403 万元，MAE=1.0135 万元。

### 5. 后端 / 前端
```bash
# 后端（gunicorn :8000，start_all.sh 已内置）
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python manage.py migrate && python manage.py collectstatic --noinput

# 前端构建（Nginx 托管 dist）
cd frontend && npm install && npm run build
```

## 核心功能

### 数据看板
- 车辆总数 / 品牌数 / 平均售价 / 预测次数统计卡片
- 品牌均价 Top10 柱状图、车龄-价格关系折线图、价格分布饼图
- 最近预测记录

### 价格预测
- 录入车辆参数（品牌、车龄、里程、变速箱、排量、燃油类型、城市、新车指导价）
- 随机森林预测 + 合理价格区间 + 置信度
- **SHAP 影响因子**：展示各特征推高/拉低价格的贡献
- 支持 sklearn / Spark MLlib 双模型

### 车辆列表 / 预测历史
- 100 万条数据分页展示、多条件筛选、排序
- 历史预测记录查询

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health/` | GET | 健康检查 |
| `/api/dashboard/summary/` | GET | 看板概览 |
| `/api/cars/` | GET | 车辆列表（分页/筛选） |
| `/api/stat/brand-price/top10/` | GET | 品牌均价 Top10 |
| `/api/stat/age-price/chart/` | GET | 车龄价格图表 |
| `/api/stat/price-distribution/chart/` | GET | 价格分布图表 |
| `/api/prediction/predict/` | POST | 价格预测（含 SHAP 解释） |
| `/api/prediction/history/` | GET | 预测历史 |
| `/api/train/start/` | POST | 触发异步重训（Celery） |
| `/api/train/status/` | GET | 训练进度查询 |

## 集群适配要点（与原单机版差异）

| 项 | 说明 |
|---|---|
| Sqoop 列错位 | MySQL 表 18 列 vs Hive ODS 14 列，必须 `--query` 精确导 14 列，否则 price 吃到日期字段导致 ETL 全量过滤为 0 |
| Spark 读 Hive 表 | `spark/conf` 需复制 `hive-site.xml`，否则连本地 derby 空 metastore |
| MariaDB 10.3 | Django 4.2 默认要求 10.4+，`settings.py` 已内置 pymysql 兼容绕过 |
| Spark 写 MySQL | 需 `mysql-connector-java-8.0.30.jar` 放 spark/jars |
| Hive ETL 引擎 | 固定 MR 引擎（`--hiveconf hive.execution.engine=mr`），Spark 引擎存在 Kryo 序列化问题 |

详见 [deploy/CLUSTER_DEPLOY.md](deploy/CLUSTER_DEPLOY.md)。

## 作者

- 姓名：刘明哲
- 专业：大数据
- 项目：二手车价格评估系统设计与实现（三机集群版）

## License

MIT
