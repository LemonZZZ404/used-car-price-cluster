#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟系统访问日志生成脚本
用于Flume采集演示，生成符合Nginx日志格式的访问日志
"""

import random
import time
import os
from datetime import datetime

random.seed(int(time.time()))

LOG_FILE = '/opt/used-car/logs/access.log'
INTERVAL = 0.5  # 每条日志间隔秒数

# 模拟URL路径
URLS = [
    '/api/car/list', '/api/car/list', '/api/car/list',
    '/api/car/detail', '/api/car/detail',
    '/api/stat/brand-price', '/api/stat/age-price',
    '/api/stat/price-distribution',
    '/api/predict', '/api/predict',
    '/api/car/search',
    '/dashboard', '/', '/car/list', '/predict',
    '/static/js/app.js', '/static/css/style.css',
    '/api/user/login', '/api/user/info'
]

METHODS = ['GET', 'GET', 'GET', 'GET', 'POST', 'POST']
STATUSES = [200, 200, 200, 200, 200, 301, 302, 404, 500]
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; MI 9) AppleWebKit/537.36',
    'PostmanRuntime/7.26.8',
    'curl/7.68.0'
]


def random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"


def generate_log():
    ip = random_ip()
    now = datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0800')
    method = random.choice(METHODS)
    url = random.choice(URLS)
    status = random.choice(STATUSES)
    size = random.randint(200, 50000)
    ua = random.choice(USER_AGENTS)
    referer = '-'
    return f'{ip} - - [{now}] "{method} {url} HTTP/1.1" {status} {size} "{referer}" "{ua}"'


def main():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    print(f"[INFO] 开始生成模拟日志，写入: {LOG_FILE}")
    print(f"[INFO] 按 Ctrl+C 停止")
    count = 0
    try:
        with open(LOG_FILE, 'a') as f:
            while True:
                line = generate_log()
                f.write(line + '\n')
                f.flush()
                count += 1
                if count % 100 == 0:
                    print(f"[INFO] 已生成 {count} 条日志")
                time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print(f"\n[DONE] 共生成 {count} 条日志")


if __name__ == '__main__':
    main()
