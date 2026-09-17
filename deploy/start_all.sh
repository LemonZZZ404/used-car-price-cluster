#!/bin/bash
# ============================================================
# 二手车价格评估系统 - 三机集群一键启动脚本
# 主控机: 192.168.249.101（执行本脚本的机器）
# 组件分布:
#   101: NameNode, DataNode, NodeManager, JobHistoryServer, ZK,
#        MySQL, Redis, Hive Metastore/HiveServer2, Django, Nginx, Celery
#   102: ResourceManager, DataNode, NodeManager, ZK
#   103: SecondaryNameNode, DataNode, NodeManager, ZK
# 用法: bash start_all.sh   （可重复执行，已运行的服务自动跳过）
# ============================================================

H1=hadoop101
H2=hadoop102
H3=hadoop103
PROJ=/opt/used-car-price-system
LOG_DIR=$PROJ/logs
mkdir -p "$LOG_DIR"

# sudo 密码（本集群环境，按需修改）
SUDO_PASSWORD="${SUDO_PASSWORD:-200412230}"
sudo_run() { echo "$SUDO_PASSWORD" | sudo -S "$@" 2>/dev/null; }

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
skip() { echo -e "${YELLOW}[跳过]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; }

port_in_use() { ss -tln 2>/dev/null | grep -q ":$1 "; }
proc_alive()  { pgrep -f "$1" > /dev/null 2>&1; }
ssh_port()    { ssh -o ConnectTimeout=8 "$1" "ss -tln 2>/dev/null | grep -q ':$2 '" 2>/dev/null; }
ssh_jps()     { ssh -o ConnectTimeout=8 "$1" "jps 2>/dev/null | grep -q '$2'" 2>/dev/null; }

echo "============================================"
echo " 二手车价格评估系统 - 三机集群 一键启动"
echo "============================================"

# ---------- 1. MySQL (101) ----------
echo "[1/9] MySQL ..."
sudo_run systemctl start mysqld > /dev/null 2>&1
sleep 2
port_in_use 3306 && ok "MySQL 已启动 (3306)" || fail "MySQL 未就绪"

# ---------- 2. Redis (101) ----------
echo "[2/9] Redis ..."
sudo_run systemctl start redis > /dev/null 2>&1
sleep 1
redis-cli ping 2>/dev/null | grep -q PONG && ok "Redis 已启动 (6379)" || fail "Redis 未就绪"

# ---------- 3. Zookeeper (三台) ----------
echo "[3/9] Zookeeper (三台) ..."
for h in $H1 $H2 $H3; do
    if ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':2181 '" 2>/dev/null; then
        skip "ZK 已在运行 ($h:2181)"
    else
        ssh -o ConnectTimeout=8 "$h" "zkServer.sh start > /dev/null 2>&1" 2>/dev/null
        sleep 3
        ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':2181 '" 2>/dev/null && ok "ZK 已启动 ($h)" || fail "ZK 启动失败 ($h)"
    fi
done

# ---------- 4. HDFS + YARN ----------
echo "[4/9] Hadoop HDFS + YARN ..."
if ssh_jps $H1 NameNode; then skip "HDFS 已在运行 (NN@101)"; else
    start-dfs.sh > /dev/null 2>&1
    sleep 6
    ssh_jps $H1 NameNode && ok "HDFS 已启动" || fail "HDFS 启动失败"
fi
if ssh_jps $H2 ResourceManager; then skip "YARN 已在运行 (RM@102)"; else
    ssh -o ConnectTimeout=8 $H2 "start-yarn.sh > /dev/null 2>&1" 2>/dev/null
    sleep 6
    ssh_jps $H2 ResourceManager && ok "YARN 已启动" || fail "YARN 启动失败"
fi

# ---------- 5. Kafka (三台) ----------
echo "[5/9] Kafka (三台) ..."
for h in $H1 $H2 $H3; do
    if ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':9092 '" 2>/dev/null; then
        skip "Kafka 已在运行 ($h:9092)"
    else
        ssh -o ConnectTimeout=8 "$h" "kafka-server-start.sh -daemon /opt/module/kafka/config/server.properties > /dev/null 2>&1" 2>/dev/null
        sleep 5
        ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':9092 '" 2>/dev/null && ok "Kafka 已启动 ($h)" || fail "Kafka 启动失败 ($h)"
    fi
done

# ---------- 6. Hive Metastore + HiveServer2 (101) ----------
echo "[6/9] Hive Metastore + HiveServer2 (101) ..."
if port_in_use 9083; then skip "Metastore 已在运行 (9083)"; else
    nohup hive --service metastore > "$LOG_DIR/metastore.log" 2>&1 &
    for i in $(seq 1 8); do sleep 5; port_in_use 9083 && break; done
    port_in_use 9083 && ok "Metastore 已启动 (9083)" || fail "Metastore 启动失败，看 $LOG_DIR/metastore.log"
fi
if port_in_use 10000; then skip "HiveServer2 已在运行 (10000)"; else
    nohup hiveserver2 > "$LOG_DIR/hiveserver2.log" 2>&1 &
    for i in $(seq 1 16); do sleep 5; port_in_use 10000 && break; done
    port_in_use 10000 && ok "HiveServer2 已启动 (10000)" || fail "HiveServer2 启动失败，看 $LOG_DIR/hiveserver2.log"
fi

# ---------- 7. Django 后端 (101) ----------
echo "[7/9] Django 后端 (gunicorn :8000) ..."
if port_in_use 8000; then skip "Django 已在运行 (8000)"; else
    cd "$PROJ/backend" || exit 1
    venv/bin/gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 --workers 2 --daemon \
        --access-logfile "$LOG_DIR/gunicorn_access.log" \
        --error-logfile "$LOG_DIR/gunicorn_error.log"
    sleep 4
    port_in_use 8000 && ok "Django 已启动 (8000)" || fail "Django 启动失败，看 $LOG_DIR/gunicorn_error.log"
fi

# ---------- 8. Nginx (101) ----------
echo "[8/9] Nginx (:80) ..."
if port_in_use 80; then skip "Nginx 已在运行 (80)"; else
    sudo_run systemctl start nginx > /dev/null 2>&1
    sleep 2
    port_in_use 80 && ok "Nginx 已启动 (80)" || fail "Nginx 启动失败"
fi

# ---------- 9. Celery (101) ----------
echo "[9/9] Celery worker ..."
if proc_alive "celery.*config worker"; then skip "Celery 已在运行"; else
    cd "$PROJ/backend" || exit 1
    venv/bin/celery -A config worker -l info --detach > "$LOG_DIR/celery.log" 2>&1
    sleep 3
    proc_alive "celery.*config worker" && ok "Celery 已启动" || fail "Celery 启动失败，看 $LOG_DIR/celery.log"
fi

# ---------- 健康检查 ----------
echo ""
echo "============================================"
echo " 健康检查"
echo "============================================"
echo "后端 API: /api/health/ -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health/ 2>/dev/null)"
echo "前端页面: http://192.168.249.101/ -> HTTP $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/ 2>/dev/null)"
IP=$(hostname -I | awk '{print $1}')
echo "访问地址: http://$IP/"
echo "系统启动完成！停止请运行: bash stop_all.sh"
