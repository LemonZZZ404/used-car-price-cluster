# 二手车价格评估系统 - 虚拟机部署文档

> 适用系统：AlmaLinux 8.x / CentOS 7.x / Ubuntu 20.04+
> 部署模式：单机伪分布式 Hadoop + Django + Vue3
> 预计部署时间：2~4小时（含环境排错）

---

## 目录

1. [环境准备](#1-环境准备)
2. [项目上传与目录结构](#2-项目上传与目录结构)
3. [MySQL 部署](#3-mysql-部署)
4. [Redis 部署](#4-redis-部署)
5. [Hadoop 伪分布式部署](#5-hadoop-伪分布式部署)
6. [Hive 部署](#6-hive-部署)
7. [Sqoop 部署](#7-sqoop-部署)
8. [Flume 部署](#8-flume-部署)
9. [Spark 部署](#9-spark-部署)
10. [数据导入与ETL流程](#10-数据导入与etl流程)
11. [Spark 数据分析与建模](#11-spark-数据分析与建模)
12. [Django 后端部署](#12-django-后端部署)
13. [Vue3 前端部署](#13-vue3-前端部署)
14. [Nginx 反向代理（可选）](#14-nginx-反向代理可选)
15. [系统验证与演示](#15-系统验证与演示)
16. [常见问题排查](#16-常见问题排查)

---

## 1. 环境准备

### 1.1 系统要求
- CPU：4核及以上
- 内存：8G及以上（推荐16G）
- 硬盘：50G及以上
- 系统：AlmaLinux 8.x（推荐）

### 1.2 基础工具安装
```bash
# AlmaLinux / CentOS
sudo dnf install -y wget curl vim git net-tools lrzsz unzip tar gcc gcc-c++ make

# Ubuntu
sudo apt update && sudo apt install -y wget curl vim git net-tools lrzsz unzip build-essential
```

### 1.3 JDK 安装（必须，所有大数据组件依赖）
```bash
# 下载 JDK 8（推荐，兼容性最好）
cd /opt
sudo wget https://repo.huaweicloud.com/java/jdk/8u202-b08/jdk-8u202-linux-x64.tar.gz
sudo tar -zxvf jdk-8u202-linux-x64.tar.gz
sudo mv jdk1.8.0_202 jdk1.8

# 配置环境变量
sudo vim /etc/profile
# 在末尾添加：
export JAVA_HOME=/opt/jdk1.8
export JRE_HOME=$JAVA_HOME/jre
export CLASSPATH=.:$JAVA_HOME/lib:$JRE_HOME/lib
export PATH=$JAVA_HOME/bin:$PATH

# 生效
source /etc/profile
java -version  # 验证
```

### 1.4 Python 3 安装
```bash
# AlmaLinux 8 自带 Python 3.6+，建议安装 3.9+
sudo dnf install -y python39 python39-devel
sudo alternatives --set python3 /usr/bin/python3.9

# 安装 pip
python3 -m ensurepip --upgrade
pip3 install --upgrade pip setuptools wheel

# 验证
python3 --version
pip3 --version
```

### 1.5 Node.js 安装（前端构建用）
```bash
cd /opt
sudo wget https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.xz
sudo tar -xvf node-v18.19.0-linux-x64.tar.xz
sudo mv node-v18.19.0-linux-x64 node


# 环境变量
sudo vim /etc/profile
# 添加：
export NODE_HOME=/opt/node
export PATH=$NODE_HOME/bin:$PATH

source /etc/profile
node -v && npm -v  # 验证

# 配置npm国内源
npm config set registry https://registry.npmmirror.com
```

---

## 2. 项目上传与目录结构

### 2.1 上传项目
将整个 `used-car-price-system` 目录上传到虚拟机 `/opt/` 下：
```bash
# 方式1：scp（在本地Windows PowerShell执行）
scp -r used-car-price-system root@<虚拟机IP>:/opt/

# 方式2：rz上传（虚拟机上执行，先打包）
# 本地先压缩为zip，然后虚拟机上 rz 上传，unzip解压

# 方式3：git clone（如果推到了git仓库）
cd /opt && git clone <你的仓库地址> used-car-price-system
```

### 2.2 最终目录结构
```
/opt/used-car-price-system/
├── data/                    # 数据层
│   ├── dataset/             # 数据集（raw + clean）
│   ├── scripts/             # 数据预处理脚本
│   └── sql/                 # MySQL建表脚本
├── bigdata/                 # 大数据层
│   ├── hive/                # Hive建表+ETL
│   ├── sqoop/               # Sqoop导入脚本
│   ├── flume/               # Flume配置+日志生成
│   └── spark/               # Spark分析+MLlib训练
├── ml/                      # 机器学习层
│   ├── models/              # 训练好的模型
│   ├── train_sklearn.py     # sklearn训练
│   └── compare_models.py    # 模型对比
├── backend/                 # Django后端
│   ├── config/              # Django配置
│   ├── car_api/             # API应用
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Vue3前端
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── deploy/                  # 部署脚本
└── docs/                    # 文档
```

### 2.3 创建日志目录
```bash
mkdir -p /opt/used-car-price-system/backend/logs
mkdir -p /opt/used-car/logs
```

---

## 3. MySQL 部署

### 3.1 安装 MySQL 8.0
```bash
# AlmaLinux 8
sudo dnf install -y @mysql:8.0
sudo systemctl start mysqld
sudo systemctl enable mysqld

# 查看临时密码
sudo grep 'temporary password' /var/log/mysqld.log

# 安全初始化
sudo mysql_secure_installation
# 按提示设置root密码，建议设为 123456（毕设演示用，简单好记）
```

### 3.2 创建数据库和表
```bash
# 登录MySQL
mysql -u root -p

# 执行建表脚本
source /opt/used-car-price-system/data/sql/init_mysql.sql;

# 验证
SHOW DATABASES;
USE used_car;
SHOW TABLES;
```

### 3.3 允许远程访问（可选，方便用Navicat连接）
```sql
USE mysql;
UPDATE user SET host='%' WHERE user='root';
FLUSH PRIVILEGES;
```

---

## 4. Redis 部署

### 4.1 安装 Redis
```bash
# AlmaLinux 8
sudo dnf install -y redis
sudo systemctl start redis
sudo systemctl enable redis

# 验证
redis-cli ping  # 返回 PONG
```

### 4.2 配置（可选）
```bash
sudo vim /etc/redis.conf
# 修改：
# bind 0.0.0.0          # 允许远程
# requirepass 123456    # 设置密码（可选）
# daemonize yes

sudo systemctl restart redis
```

---

## 5. Hadoop 伪分布式部署

### 5.1 下载解压
```bash
cd /opt
sudo wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz
sudo tar -zxvf hadoop-3.3.4.tar.gz
sudo mv hadoop-3.3.4 hadoop
sudo chown -R $USER:$USER /opt/hadoop
```

### 5.2 环境变量
```bash
sudo vim /etc/profile
# 添加：
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export HDFS_SECONDARYNAMENODE_USER=root
export YARN_RESOURCEMANAGER_USER=root
export YARN_NODEMANAGER_USER=root

source /etc/profile
hadoop version  # 验证
```

### 5.3 配置 SSH 免密登录
```bash
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
ssh localhost  # 验证，不需要输入密码
```

### 5.4 核心配置文件

**（1）core-site.xml**
```bash
vim /opt/hadoop/etc/hadoop/core-site.xml
```
```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/opt/hadoop/tmp</value>
    </property>
</configuration>
```

**（2）hdfs-site.xml**
```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/opt/hadoop/tmp/dfs/name</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/opt/hadoop/tmp/dfs/data</value>
    </property>
</configuration>
```

**（3）yarn-site.xml**
```xml
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.memory-mb</name>
        <value>4096</value>
    </property>
    <property>
        <name>yarn.scheduler.maximum-allocation-mb</name>
        <value>4096</value>
    </property>
</configuration>
```

**（4）mapred-site.xml**
```xml
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

**（5）hadoop-env.sh**
```bash
echo 'export JAVA_HOME=/opt/jdk1.8' >> /opt/hadoop/etc/hadoop/hadoop-env.sh
```

### 5.5 格式化并启动
```bash
# 格式化NameNode（只执行一次！）
hdfs namenode -format

# 启动HDFS
start-dfs.sh

# 启动YARN
start-yarn.sh

# 验证进程（应该有6个：NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager, Jps）
jps

# Web UI
# HDFS: http://<虚拟机IP>:9870
# YARN: http://<虚拟机IP>:8088
```

### 5.6 创建HDFS目录
```bash
hdfs dfs -mkdir -p /user/hive/warehouse/used_car/ods/ods_car_info
hdfs dfs -mkdir -p /user/hive/warehouse/used_car/ods/ods_access_log
hdfs dfs -mkdir -p /user/hive/warehouse/used_car/dwd
hdfs dfs -mkdir -p /user/hive/warehouse/used_car/ads
hdfs dfs -chmod -R 777 /user/hive
```

---

## 6. Hive 部署

### 6.1 下载解压
```bash
cd /opt
sudo wget https://archive.apache.org/dist/hive/hive-3.1.3/apache-hive-3.1.3-bin.tar.gz
sudo tar -zxvf apache-hive-3.1.3-bin.tar.gz
sudo mv apache-hive-3.1.3-bin hive
sudo chown -R $USER:$USER /opt/hive
```

### 6.2 环境变量
```bash
sudo vim /etc/profile
# 添加：
export HIVE_HOME=/opt/hive
export PATH=$PATH:$HIVE_HOME/bin

source /etc/profile
hive --version  # 验证
```

### 6.3 配置 hive-site.xml
```bash
vim /opt/hive/conf/hive-site.xml
```
```xml
<configuration>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:mysql://localhost:3306/hive_metadata?createDatabaseIfNotExist=true&useSSL=false&characterEncoding=utf-8</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionDriverName</name>
        <value>com.mysql.cj.jdbc.Driver</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionUserName</name>
        <value>root</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionPassword</name>
        <value>123456</value>
    </property>
    <property>
        <name>hive.metastore.warehouse.dir</name>
        <value>/user/hive/warehouse</value>
    </property>
    <property>
        <name>hive.exec.scratchdir</name>
        <value>/tmp/hive</value>
    </property>
    <property>
        <name>hive.server2.thrift.port</name>
        <value>10000</value>
    </property>
</configuration>
```

### 6.4 拷贝 MySQL 驱动
```bash
# 下载 mysql-connector-java
cd /opt
wget https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.30/mysql-connector-java-8.0.30.jar
cp mysql-connector-java-8.0.30.jar /opt/hive/lib/

# 同时给Sqoop也拷贝一份（后面用）
mkdir -p /opt/sqoop/lib
cp mysql-connector-java-8.0.30.jar /opt/sqoop/lib/
```

### 6.5 初始化元数据库
```bash
# 在MySQL中创建hive元数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS hive_metadata DEFAULT CHARSET utf8mb4;"

# 初始化Hive元数据
schematool -dbType mysql -initSchema

# 验证
hive -e "SHOW DATABASES;"
```

> **常见坑**：如果报 `Guava` 版本冲突，删除 Hive 自带的低版本 guava：
> ```bash
> rm /opt/hive/lib/guava-19.0.jar
> cp /opt/hadoop/share/hadoop/hdfs/lib/guava-27.0-jre.jar /opt/hive/lib/
> ```

---

## 7. Sqoop 部署

### 7.1 下载解压
```bash
cd /opt
sudo wget https://archive.apache.org/dist/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz
sudo tar -zxvf sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz
sudo mv sqoop-1.4.7.bin__hadoop-2.6.0 sqoop
sudo chown -R $USER:$USER /opt/sqoop
```

### 7.2 环境变量
```bash
sudo vim /etc/profile
# 添加：
export SQOOP_HOME=/opt/sqoop
export PATH=$PATH:$SQOOP_HOME/bin

source /etc/profile
sqoop version  # 验证
```

### 7.3 配置
```bash
# 拷贝配置模板
cp /opt/sqoop/conf/sqoop-env-template.sh /opt/sqoop/conf/sqoop-env.sh
vim /opt/sqoop/conf/sqoop-env.sh
# 修改：
export HADOOP_COMMON_HOME=/opt/hadoop
export HADOOP_MAPRED_HOME=/opt/hadoop
export HIVE_HOME=/opt/hive
```

> **注意**：MySQL驱动已在6.4步拷贝到 `/opt/sqoop/lib/`

---

## 8. Flume 部署

### 8.1 下载解压
```bash
cd /opt
sudo wget https://archive.apache.org/dist/flume/1.11.0/apache-flume-1.11.0-bin.tar.gz
sudo tar -zxvf apache-flume-1.11.0-bin.tar.gz
sudo mv apache-flume-1.11.0-bin flume
sudo chown -R $USER:$USER /opt/flume
```

### 8.2 环境变量
```bash
sudo vim /etc/profile
# 添加：
export FLUME_HOME=/opt/flume
export PATH=$PATH:$FLUME_HOME/bin

source /etc/profile
flume-ng version  # 验证
```

### 8.3 配置
```bash
cp /opt/flume/conf/flume-env.sh.template /opt/flume/conf/flume-env.sh
echo 'export JAVA_HOME=/opt/jdk1.8' >> /opt/flume/conf/flume-env.sh
```

---

## 9. Spark 部署

### 9.1 下载解压
```bash
cd /opt
# 选择带Hadoop的预编译包
sudo wget https://archive.apache.org/dist/spark/spark-3.3.2/spark-3.3.2-bin-hadoop3.tgz
sudo tar -zxvf spark-3.3.2-bin-hadoop3.tgz
sudo mv spark-3.3.2-bin-hadoop3 spark
sudo chown -R $USER:$USER /opt/spark
```

### 9.2 环境变量
```bash
sudo vim /etc/profile
# 添加：
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3

source /etc/profile
spark-submit --version  # 验证
```

### 9.3 配置 Spark 连接 Hive
```bash
# 让Spark能读取Hive表
cp /opt/hive/conf/hive-site.xml /opt/spark/conf/

# 配置 spark-defaults.conf
cp /opt/spark/conf/spark-defaults.conf.template /opt/spark/conf/spark-defaults.conf
vim /opt/spark/conf/spark-defaults.conf
# 添加：
spark.master                     local[*]
spark.driver.memory              2g
spark.executor.memory            2g
spark.sql.warehouse.dir          /user/hive/warehouse
spark.serializer                 org.apache.spark.serializer.KryoSerializer
```

### 9.4 安装 PySpark（Python端）
```bash
pip3 install pyspark==3.3.2 findspark
```

---

## 10. 数据导入与ETL流程

### 10.1 生成模拟数据（如果没有真实数据集）
```bash
cd /opt/used-car-price-system
pip3 install pandas numpy
python3 data/scripts/generate_mock_data.py
# 生成 data/dataset/raw_car_data.csv，约20000条
```

### 10.2 数据预处理
```bash
python3 data/scripts/data_preprocess.py --mysql
# 生成清洗后数据 data/dataset/clean_car_data.csv
# 同时导入MySQL的car_info表
```

### 10.3 上传原始数据到HDFS
```bash
hdfs dfs -put -f /opt/used-car-price-system/data/dataset/raw_car_data.csv \
  /user/hive/warehouse/used_car/ods/ods_car_info/

hdfs dfs -ls /user/hive/warehouse/used_car/ods/ods_car_info/
```

### 10.4 方式A：Sqoop 从MySQL导入HDFS（推荐，体现Sqoop）
```bash
cd /opt/used-car-price-system
bash bigdata/sqoop/sqoop_import.sh
# 该脚本会把MySQL的car_info表数据导入HDFS
```

### 10.5 Hive 建表
```bash
hive -f bigdata/hive/create_tables.hql
```

### 10.6 Hive ETL 清洗
```bash
hive -f bigdata/hive/etl_clean.hql --hivevar dt=20240101
# 执行后会生成 dwd_car_info 清洗表，以及3张统计汇总表
```

### 10.7 Flume 日志采集（可选演示）
```bash
# 终端1：启动日志生成
mkdir -p /opt/used-car/logs
python3 bigdata/flume/generate_access_log.py &

# 终端2：启动Flume
flume-ng agent -n a1 -c /opt/flume/conf \
  -f /opt/used-car-price-system/bigdata/flume/flume_hdfs.conf

# 验证HDFS上有日志文件
hdfs dfs -ls -R /user/hive/warehouse/used_car/ods/ods_access_log/
```

---

## 11. Spark 数据分析与建模

### 11.1 Spark SQL 数据分析
```bash
cd /opt/used-car-price-system

# 方式1：spark-submit提交
spark-submit --master local[*] \
  --jars /opt/hive/lib/mysql-connector-java-8.0.30.jar \
  bigdata/spark/spark_analysis.py

# 方式2：直接python运行（需配置好SPARK_HOME）
python3 bigdata/spark/spark_analysis.py
```
> 执行后会把统计结果写入MySQL的 `stat_brand_price`、`stat_age_price`、`stat_price_distribution` 表

### 11.2 Spark MLlib 模型训练
```bash
spark-submit --master local[*] bigdata/spark/spark_mllib_train.py
# 训练完成后模型保存在 /tmp/spark_mllib_rf_model
# 评估指标保存在 ml/models/spark_mllib_metrics.json
```

### 11.3 Scikit-learn 模型训练（Django后端用这个模型）
```bash
pip3 install scikit-learn pandas numpy joblib
cd /opt/used-car-price-system
python3 ml/train_sklearn.py
# 训练完成后：
# 模型文件：ml/models/rf_price_model.joblib
# 评估指标：ml/models/sklearn_metrics.json
```

### 11.4 模型对比
```bash
python3 ml/compare_models.py
# 生成 ml/models/model_comparison.md，可直接放进论文
```

---

## 12. Django 后端部署

### 12.1 安装依赖
```bash
cd /opt/used-car-price-system/backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 如果mysqlclient安装失败，先装系统依赖：
# AlmaLinux: dnf install -y mysql-devel python3-devel
# Ubuntu: apt install -y libmysqlclient-dev python3-dev
```

### 12.2 配置环境变量
```bash
cp .env.example .env
vim .env
# 根据实际情况修改MySQL密码、Redis地址、模型路径等
# 关键：SKLEARN_MODEL_PATH 要指向训练好的模型
# SKLEARN_MODEL_PATH=/opt/used-car-price-system/ml/models/rf_price_model.joblib
```

### 12.3 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate

# 创建管理员
python manage.py createsuperuser
# 用户名: admin  邮箱: admin@example.com  密码: admin123
```

### 12.4 启动开发服务器（测试用）
```bash
python manage.py runserver 0.0.0.0:8000
# 访问 http://<虚拟机IP>:8000/api/health/ 验证
# 接口文档 http://<虚拟机IP>:8000/swagger/
# Admin后台 http://<虚拟机IP>:8000/admin/
```

### 12.5 生产启动（Gunicorn，推荐）
```bash
# 启动Gunicorn（4个worker）
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile /opt/used-car-price-system/backend/logs/gunicorn_access.log \
  --error-logfile /opt/used-car-price-system/backend/logs/gunicorn_error.log \
  --daemon

# 查看进程
ps aux | grep gunicorn

# 停止
pkill gunicorn
```

### 12.6 后端接口清单
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health/` | GET | 健康检查 |
| `/api/dashboard/summary/` | GET | 看板概览数据 |
| `/api/cars/` | GET | 车辆列表（分页+筛选） |
| `/api/cars/brands/` | GET | 品牌列表 |
| `/api/cars/search/` | GET | 高级搜索 |
| `/api/stat/brand-price/top10/` | GET | 品牌均价Top10（ECharts） |
| `/api/stat/age-price/chart/` | GET | 车龄-价格图表数据 |
| `/api/stat/price-distribution/chart/` | GET | 价格分布图表数据 |
| `/api/prediction/predict/` | POST | 价格预测（核心接口） |
| `/api/prediction/history/` | GET | 预测历史 |
| `/api/prediction/model-info/` | GET | 模型信息 |
| `/swagger/` | GET | 接口文档 |

---

## 13. Vue3 前端部署

### 13.1 安装依赖
```bash
cd /opt/used-car-price-system/frontend
npm install
# 如果慢，确认已配置npmmirror源
```

### 13.2 开发模式运行（测试用）
```bash
npm run dev
# 访问 http://<虚拟机IP>:5173
# vite已配置代理，/api请求会转发到localhost:8000
```

### 13.3 生产构建
```bash
npm run build
# 构建产物在 dist/ 目录
```

### 13.4 部署到Nginx（推荐）
见下一节。

---

## 14. Nginx 反向代理（可选）

### 14.1 安装 Nginx
```bash
sudo dnf install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 14.2 配置
```bash
sudo vim /etc/nginx/conf.d/used-car.conf
```
```nginx
server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root /opt/used-car-price-system/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # Django静态文件（admin后台等）
    location /static/ {
        alias /opt/used-car-price-system/backend/staticfiles/;
    }
}
```

```bash
# 收集Django静态文件
cd /opt/used-car-price-system/backend
python manage.py collectstatic --noinput

# 测试配置并重载
sudo nginx -t
sudo systemctl reload nginx

# 防火墙放行80端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

现在访问 `http://<虚拟机IP>` 即可直接打开系统。

---

## 15. 系统验证与演示

### 15.1 启动顺序（每次开机后）
```bash
# 1. 启动MySQL
sudo systemctl start mysqld

# 2. 启动Redis
sudo systemctl start redis

# 3. 启动Hadoop
start-dfs.sh && start-yarn.sh

# 4. 启动Hive Metastore（可选）
nohup hive --service metastore &

# 5. 启动Django后端
cd /opt/used-car-price-system/backend
source venv/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --daemon

# 6. 启动前端（开发模式）或用Nginx
cd /opt/used-car-price-system/frontend
npm run dev  # 或已部署Nginx则不需要
```

### 15.2 演示流程（答辩用）
1. **数据看板**：展示4个统计卡片 + 3个ECharts图表（品牌均价、车龄价格、价格分布）
2. **价格预测**：输入车辆参数（品牌、车龄、里程等），点击预测，展示预测价格和合理区间
3. **车辆列表**：展示二手车数据，支持多条件筛选搜索
4. **预测历史**：展示历史预测记录
5. **大数据流程演示**（可选）：
   - 展示HDFS Web UI（9870）上的数据文件
   - 展示Hive表数据
   - 展示Spark任务运行日志
   - 展示Flume采集的日志文件

### 15.3 一键启动脚本
项目 `deploy/` 目录下提供了启动脚本，详见 `deploy/start_all.sh`。

---

## 16. 常见问题排查

### Q1: Hadoop 启动后 DataNode 没起来
**原因**：多次格式化NameNode导致clusterID不一致
**解决**：
```bash
stop-dfs.sh
rm -rf /opt/hadoop/tmp
hdfs namenode -format
start-dfs.sh
```

### Q2: Hive 启动报 `MetaException` 或连接MySQL失败
**原因**：MySQL驱动没放对位置，或hive-site.xml配置错误
**解决**：
- 确认 `/opt/hive/lib/mysql-connector-java-8.0.30.jar` 存在
- 确认MySQL中 `hive_metadata` 数据库已创建
- 重新执行 `schematool -dbType mysql -initSchema`

### Q3: Sqoop 报 `ClassNotFoundException: com.mysql.cj.jdbc.Driver`
**原因**：MySQL驱动没放到sqoop/lib
**解决**：`cp mysql-connector-java-8.0.30.jar /opt/sqoop/lib/`

### Q4: Spark 读取Hive表报错 `Table not found`
**原因**：Spark没有正确配置Hive
**解决**：
- 确认 `hive-site.xml` 已拷贝到 `/opt/spark/conf/`
- 确认 `spark.sql.warehouse.dir` 配置正确
- 代码中使用 `spark.sql("USE used_car")` 或写全表名

### Q5: Django 连MySQL报 `Access denied`
**原因**：MySQL密码不对，或用户没有远程访问权限
**解决**：检查 `.env` 中的密码，或在MySQL中授权：
```sql
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '123456';
FLUSH PRIVILEGES;
```

### Q6: 预测接口返回500，日志显示模型加载失败
**原因**：模型文件路径不对，或模型文件不存在
**解决**：
- 确认 `ml/models/rf_price_model.joblib` 存在
- 确认 `.env` 中 `SKLEARN_MODEL_PATH` 是绝对路径且正确
- 如果模型不存在，先运行 `python ml/train_sklearn.py` 训练

### Q7: 前端页面空白或接口404
**原因**：API代理配置错误，或后端没启动
**解决**：
- 确认后端 `http://localhost:8000/api/health/` 能访问
- 开发模式下检查 `vite.config.js` 中的proxy配置
- 生产模式下检查Nginx配置

### Q8: 虚拟机内存不足，Spark/Hive任务OOM
**原因**：分配内存太小
**解决**：
- 虚拟机分配至少8G内存
- 减少Spark executor内存：`spark.executor.memory=1g`
- 减少数据量：用5000条数据代替20000条
- 关闭不必要的进程（如GUI桌面）

### Q9: `pip install mysqlclient` 失败
**原因**：缺少系统依赖
**解决**：
```bash
# AlmaLinux/CentOS
sudo dnf install -y mysql-devel python3-devel gcc
# Ubuntu
sudo apt install -y libmysqlclient-dev python3-dev default-libmysqlclient-dev build-essential
```

### Q10: 端口被占用
```bash
# 查看端口占用
netstat -tlnp | grep 8000
# 杀掉进程
kill -9 <PID>
```

---

## 附：版本兼容性参考（已验证可用）

| 组件 | 版本 | 说明 |
|------|------|------|
| JDK | 1.8_202 | 必须，所有组件依赖 |
| Hadoop | 3.3.4 | 伪分布式 |
| Hive | 3.1.3 | 元数据存MySQL |
| Sqoop | 1.4.7 | 需hadoop-2.6.0编译版 |
| Flume | 1.11.0 | |
| Spark | 3.3.2 | 预编译hadoop3版 |
| PySpark | 3.3.2 | 与Spark版本一致 |
| MySQL | 8.0.x | |
| Redis | 6.x/7.x | |
| Python | 3.9+ | |
| Node.js | 18.x | |
| Django | 4.2.x | |
| Vue | 3.4.x | |
| ECharts | 5.5.x | |

---

> **部署完成标志**：
> 1. 浏览器访问 `http://<虚拟机IP>` 能打开系统首页
> 2. 数据看板能显示统计卡片和图表
> 3. 价格预测页面输入参数后能返回预测价格
> 4. 车辆列表能显示数据
> 5. `http://<虚拟机IP>:9870` 能打开HDFS Web UI
