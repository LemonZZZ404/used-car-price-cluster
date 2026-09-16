# 二手车价格评估系统 — 三机集群版部署文档

> 本仓库为原 used-car-price-system 的**集群部署版**：在大数据三机集群上跑通"数据采集 → 数仓分层 → Spark 分析 → Web 展示"全链路。

## 1. 集群环境

| 主机 | IP | 角色 |
|---|---|---|
| hadoop101 | 192.168.249.101 | NameNode / JobHistoryServer / Hive Metastore / HiveServer2 / MySQL / Redis / Django / Nginx / Celery |
| hadoop102 | 192.168.249.102 | ResourceManager |
| hadoop103 | 192.168.249.103 | SecondaryNameNode |

- 普通用户：`gk / gk`，root：`root / 200412230`
- 软件目录：`/opt/module`（hadoop-3.1.3、zookeeper-3.5.7、kafka、flume、sqoop、hive-3.1.2、spark-3.0.0、mysql）
- MySQL：`192.168.249.101:3306`，库 `used_car`，root 密码按环境配置
- 三台机 SSH 免密已配置（`hadoop101` → `hadoop102/103`）

## 2. 数据规模

- MySQL `car_info`：1,000,000 条车辆数据
- Hive DWD 层：999,998 条（清洗后）
- 训练数据：500,000 条抽样

## 3. 数据链路

```
MySQL car_info (100万条)
   │ ① Sqoop --query 精确导 14 列
   ▼
HDFS ODS /user/hive/warehouse/used_car/ods/ods_car_info (999,999 条)
   │ ② Hive MR ETL（etl_clean.hql，MR 引擎）
   ▼
Hive DWD dwd_car_info (999,998 条, dt=20240101)
   │ ③ Spark SQL 分析（spark_analysis.py → MySQL stat_* 三表）
   ▼
MySQL stat_brand_price / stat_age_price / stat_price_distribution
   │ ④ Django REST API
   ▼
Vue3 前端（Nginx :80 反代 /api → :8000）
```

## 4. 一键启动 / 停止

```bash
# 在 hadoop101 上（任意位置）
bash /opt/used-car-price-cluster/deploy/start_all.sh   # 幂等，已运行自动跳过
bash /opt/used-car-price-cluster/deploy/stop_all.sh    # 反向停止
```

启动顺序：MySQL → Redis → ZK(3台) → HDFS/YARN → Kafka(3台) → Hive(Meta/HS2) → Django → Nginx → Celery
停止顺序：Celery → Django → Nginx → Hive → Kafka → YARN/HDFS → ZK → Redis（MySQL 默认不停）

访问：`http://192.168.249.101/`

## 5. 手工跑批（数据更新后）

```bash
# ① Sqoop 重新导入（14 列对齐，避免列错位）
bash bigdata/sqoop/sqoop_import.sh

# ② Hive ETL（MR 引擎，写入 DWD + ADS 三表）
cd /opt/used-car-price-system
beeline -u "jdbc:hive2://hadoop101:10000/default" -n gk -p gk --silent=true \
  -f bigdata/hive/etl_clean.hql --hivevar dt=20240101 --hiveconf hive.execution.engine=mr

# ③ Spark 分析写 MySQL stat_*（环境变量覆盖主机/密码/内存）
cd bigdata/spark
MYSQL_PASSWORD='200412230' \
spark-submit --master yarn --deploy-mode client \
  --jars /opt/module/spark/jars/mysql-connector-java-8.0.30.jar \
  spark_analysis.py
```

## 6. 集群适配要点（与原单机版差异）

| 项 | 说明 |
|---|---|
| Sqoop 列错位 | MySQL car_info 18 列（含 id 等），Hive ODS 只建 14 列。必须 `--query`/`--columns` 精确导 14 列，否则 price 吃日期字段、WHERE 全过滤 → DWD 0 行 |
| Spark 读不到 Hive 表 | `spark/conf` 需有 `hive-site.xml`（cp /opt/module/hive/conf/hive-site.xml /opt/module/spark/conf/），否则 Spark 连本地 derby 空 metastore |
| MariaDB 10.3 | Django 4.2 默认要求 10.4+，settings.py 已用 pymysql 并绕过版本检查 |
| prediction_record | 若由 init_mysql.sql 旧结构建表（缺 city/original_price 列），需按 Django 模型重建：DROP 后 `manage.py sqlmigrate car_api 0001` 提取建表语句执行 |
| MySQL 驱动 | Spark 写 MySQL 需 mysql-connector-java-8.0.30.jar（放 /opt/module/spark/jars/） |
| 内存 | 三台机 3.5G，Spark driver/executor 设 512m（spark_analysis.py 环境变量可调） |

## 7. 前端 / 后端

- 后端：Django 4.2 + DRF + gunicorn(:8000) + Celery(:6379/1) + Redis 缓存
- 前端：Vue3 + Vite + ECharts + Element Plus，`npm run build` 产物由 Nginx 托管
- 功能：车辆列表/搜索、看板统计、价格预测（随机森林 + SHAP 影响因子）、一键重训（Celery 异步）、模型分析页

## 8. 模型

- 训练：`python ml/train_sklearn.py`（读 data/dataset/clean_car_data.csv，500,000 条抽样）
- 结果：RandomForest R²=0.9323，RMSE=1.403 万元，MAE=1.0135 万元
- 产物（不入库）：`ml/models/*.joblib`
