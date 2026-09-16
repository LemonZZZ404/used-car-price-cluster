"""
Celery 异步任务 - 模型训练
实现：一键重训（subprocess 独立进程跑训练脚本，避免占用 worker 内存）
状态：写入 ml/models/train_status.json，前端轮询查看
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

from celery import shared_task
from django.conf import settings

# 项目根目录（/opt/used-car-price-system）
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 兼容：BASE_DIR 为 backend 目录，其 parent 是项目根
if PROJECT_DIR.endswith('backend'):
    PROJECT_DIR = os.path.dirname(PROJECT_DIR)

TRAIN_SCRIPT = os.path.join(PROJECT_DIR, 'ml', 'train_sklearn.py')
MODEL_DIR = os.path.join(PROJECT_DIR, 'ml', 'models')
STATUS_FILE = os.path.join(MODEL_DIR, 'train_status.json')
METRICS_FILE = os.path.join(MODEL_DIR, 'sklearn_metrics.json')
LOG_FILE = os.path.join(PROJECT_DIR, 'backend', 'logs', 'train_task.log')


def _write_status(status, progress, message, metrics=None):
    """写入训练状态"""
    data = {
        'status': status,          # idle / running / success / error
        'progress': progress,      # 0-100
        'message': message,
        'metrics': metrics or {},
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    try:
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


@shared_task(bind=True)
def run_training_task(self):
    """执行模型训练（异步）"""
    _write_status('running', 5, '训练任务已启动，正在准备环境...')

    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        # 用独立进程执行训练脚本，避免占用 Celery worker 内存
        with open(LOG_FILE, 'w', encoding='utf-8') as logf:
            proc = subprocess.Popen(
                # -u: 无缓冲输出，保证日志实时刷新（进度条依赖）
                [sys.executable, '-u', TRAIN_SCRIPT],
                stdout=logf,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_DIR,
            )

        # 轮询训练进程，同时读取日志更新进度
        progress_stage = 10
        last_progress = 10
        last_message = '正在加载数据并训练模型...'
        while proc.poll() is None:
            time.sleep(3)
            try:
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                # 根据日志内容估算进度
                if '数据加载完成' in content and last_progress < 20:
                    last_progress = 20
                    last_message = '数据加载完成，正在特征工程...'
                if '开始训练' in content and last_progress < 40:
                    last_progress = 40
                    last_message = '模型训练中（随机森林 100 棵树）...'
                if '训练完成' in content and last_progress < 70:
                    last_progress = 70
                    last_message = '训练完成，正在评估模型...'
                if '评估' in content and last_progress < 85:
                    last_progress = 85
                    last_message = '评估完成，正在保存模型...'
                if last_progress != progress_stage:
                    progress_stage = last_progress
                    _write_status('running', progress_stage, last_message)
            except Exception:
                pass

        rc = proc.returncode
        if rc != 0:
            _write_status('error', 100, f'训练失败（退出码 {rc}），详见 backend/logs/train_task.log')
            return

        # 读取训练指标
        metrics = {}
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
            except Exception:
                pass

        _write_status('success', 100, '训练完成，模型已更新', metrics)
    except Exception as e:
        _write_status('error', 100, f'训练任务异常: {str(e)}')
