#!/bin/bash
# ============================================================
# 二手车价格评估系统 - 三机集群一键停止脚本
# 反向于 start_all.sh，幂等执行
# 用法: bash stop_all.sh
# ============================================================

H1=hadoop101
H2=hadoop102
H3=hadoop103
PROJ=/opt/used-car-price-system
SUDO_PASSWORD="${SUDO_PASSWORD:-200412230}"
sudo_run() { echo "$SUDO_PASSWORD" | sudo -S "$@" 2>/dev/null; }

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
skip() { echo -e "${YELLOW}[跳过]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; }

port_in_use() { ss -tln 2>/dev/null | grep -q ":$1 "; }
proc_alive()  { pgrep -f "$1" > /dev/null 2>&1; }

echo "============================================"
echo " 二手车价格评估系统 - 三机集群 一键停止"
echo "============================================"

# ---------- 1. 应用层：Celery / Django / Nginx (101) ----------
echo "[1/6] 停止应用层 (Celery/Django/Nginx) ..."
if proc_alive "celery.*config worker"; then pkill -f "celery.*config worker"; sleep 1; ok "Celery 已停止"; else skip "Celery 未运行"; fi
if port_in_use 8000; then fuser -k 8000/tcp > /dev/null 2>&1 || pkill -f "gunicorn.*config.wsgi"; sleep 2; port_in_use 8000 && fail "Django 8000 仍被占用" || ok "Django 已停止"; else skip "Django 未运行"; fi
if port_in_use 80; then sudo_run systemctl stop nginx > /dev/null 2>&1; sleep 1; port_in_use 80 && fail "Nginx 80 仍被占用" || ok "Nginx 已停止"; else skip "Nginx 未运行"; fi

# ---------- 2. Hive：HS2 / Metastore (101) ----------
echo "[2/6] 停止 Hive (HS2/Metastore) ..."
if port_in_use 10000; then pkill -f "hiveserver2"; sleep 3; port_in_use 10000 && fail "HS2 10000 仍被占用" || ok "HiveServer2 已停止"; else skip "HiveServer2 未运行"; fi
if port_in_use 9083; then pkill -f "metastore"; sleep 3; port_in_use 9083 && fail "Metastore 9083 仍被占用" || ok "Metastore 已停止"; else skip "Metastore 未运行"; fi

# ---------- 3. Kafka (三台) ----------
echo "[3/6] 停止 Kafka (三台) ..."
for h in $H1 $H2 $H3; do
    if ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':9092 '" 2>/dev/null; then
        ssh -o ConnectTimeout=8 "$h" "kafka-server-stop.sh > /dev/null 2>&1" 2>/dev/null
        sleep 4
        ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':9092 '" 2>/dev/null && fail "Kafka 未停止 ($h)" || ok "Kafka 已停止 ($h)"
    else
        skip "Kafka 未运行 ($h)"
    fi
done

# ---------- 4. YARN + HDFS ----------
echo "[4/6] 停止 Hadoop (YARN/HDFS) ..."
if ssh -o ConnectTimeout=8 $H2 "jps 2>/dev/null | grep -q ResourceManager" 2>/dev/null; then
    ssh -o ConnectTimeout=8 $H2 "stop-yarn.sh > /dev/null 2>&1" 2>/dev/null
    sleep 4
    ok "YARN 已停止"
else
    skip "YARN 未运行"
fi
if ssh -o ConnectTimeout=8 $H1 "jps 2>/dev/null | grep -q NameNode" 2>/dev/null; then
    stop-dfs.sh > /dev/null 2>&1
    sleep 4
    ok "HDFS 已停止"
else
    skip "HDFS 未运行"
fi

# ---------- 5. Zookeeper (三台) ----------
echo "[5/6] 停止 Zookeeper (三台) ..."
for h in $H1 $H2 $H3; do
    if ssh -o ConnectTimeout=8 "$h" "ss -tln 2>/dev/null | grep -q ':2181 '" 2>/dev/null; then
        ssh -o ConnectTimeout=8 "$h" "zkServer.sh stop > /dev/null 2>&1" 2>/dev/null
        sleep 2
        ok "ZK 已停止 ($h)"
    else
        skip "ZK 未运行 ($h)"
    fi
done

# ---------- 6. Redis / MySQL (101，可选) ----------
echo "[6/6] 停止 Redis / MySQL ..."
if redis-cli ping 2>/dev/null | grep -q PONG; then sudo_run systemctl stop redis > /dev/null 2>&1; ok "Redis 已停止"; else skip "Redis 未运行"; fi
if port_in_use 3306; then
    echo "  MySQL 默认不停止（数据服务），如需停止: sudo systemctl stop mysqld"
else
    skip "MySQL 未运行"
fi

echo ""
echo "系统已全部停止（MySQL 除外，Nginx 已停）"
