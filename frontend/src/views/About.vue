<template>
  <div>
    <!-- 项目简介 -->
    <div class="card" style="margin-bottom:20px">
      <div class="card-title">
        <span>项目简介</span>
        <el-tag type="primary" effect="light" size="small" round>毕业设计 / 全栈 + 大数据</el-tag>
      </div>
      <p class="intro-text">
        二手车价格评估系统是一套<strong>前后端分离 + 大数据全链路</strong>的智能评估平台：基于
        <strong>999,999 条</strong>真实模拟车辆交易数据，构建 Scikit-learn 随机森林价格预测模型（R² = 0.9323），
        支持 SHAP 特征可解释分析、Celery 异步一键重训；数据经 Sqoop 采集入 HDFS，Hive 分层建模（ODS → DWD），
        Spark SQL 聚合分析，最终通过 Django REST API 供 Vue3 看板与预测页面使用。系统已从单机版演进为
        <strong>三机分布式集群</strong>部署（Hadoop / Hive / Spark / ZooKeeper / Kafka）。
      </p>
      <div class="intro-highlights">
        <div class="hl-item">
          <div class="hl-icon" style="background:linear-gradient(135deg,#2D6BFF,#5B8CFF)">
            <el-icon :size="22"><DataAnalysis /></el-icon>
          </div>
          <div class="hl-info">
            <div class="hl-title">百万级数据</div>
            <div class="hl-desc">999,999 条车辆交易样本</div>
          </div>
        </div>
        <div class="hl-item">
          <div class="hl-icon" style="background:linear-gradient(135deg,#22C55E,#4ADE80)">
            <el-icon :size="22"><MagicStick /></el-icon>
          </div>
          <div class="hl-info">
            <div class="hl-title">SHAP 可解释</div>
            <div class="hl-desc">预测结果展示价格影响因子</div>
          </div>
        </div>
        <div class="hl-item">
          <div class="hl-icon" style="background:linear-gradient(135deg,#F59E0B,#FBBF24)">
            <el-icon :size="22"><Refresh /></el-icon>
          </div>
          <div class="hl-info">
            <div class="hl-title">异步重训</div>
            <div class="hl-desc">Celery 一键重训 + 实时进度</div>
          </div>
        </div>
        <div class="hl-item">
          <div class="hl-icon" style="background:linear-gradient(135deg,#EF4444,#F87171)">
            <el-icon :size="22"><Platform /></el-icon>
          </div>
          <div class="hl-info">
            <div class="hl-title">分布式集群</div>
            <div class="hl-desc">三机 Hadoop/Hive/Spark 部署</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模型表现 + 仓库 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="14">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title">
            <span>模型表现</span>
            <el-tag type="success" effect="light" size="small" round>当前生产模型</el-tag>
          </div>
          <el-table :data="modelRows" size="small" stripe border>
            <el-table-column prop="metric" label="指标" width="160" />
            <el-table-column prop="value" label="数值" width="140">
              <template #default="{ row }">
                <span style="font-weight:700;color:#2D6BFF">{{ row.value }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="desc" label="说明">
              <template #default="{ row }">
                <span style="color:#6B7280;font-size:12.5px">{{ row.desc }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :md="10">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title">
            <span>仓库与部署</span>
            <el-tag type="warning" effect="light" size="small" round>GitHub</el-tag>
          </div>
          <div class="repo-list">
            <a class="repo-item" href="https://github.com/LemonZZZ404/used-car-price-cluster" target="_blank">
              <div class="repo-icon"><el-icon :size="18"><Connection /></el-icon></div>
              <div>
                <div class="repo-name">used-car-price-cluster</div>
                <div class="repo-desc">集群版（三机分布式部署）</div>
              </div>
            </a>
            <a class="repo-item" href="https://github.com/LemonZZZ404/used-car-price-system" target="_blank">
              <div class="repo-icon" style="background:linear-gradient(135deg,#7C3AED,#A78BFA)"><el-icon :size="18"><Connection /></el-icon></div>
              <div>
                <div class="repo-name">used-car-price-system</div>
                <div class="repo-desc">单机版（全功能基线）</div>
              </div>
            </a>
          </div>
          <div class="deploy-note">
            <el-icon style="margin-right:6px;color:#22C55E"><CircleCheckFilled /></el-icon>
            <span>一键启动：<code>bash deploy/start_all.sh</code>（9 项服务幂等启动）</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 功能清单 -->
    <div class="card">
      <div class="card-title">
        <span>核心功能</span>
        <el-tag type="info" effect="light" size="small" round>6 大模块</el-tag>
      </div>
      <el-row :gutter="16">
        <el-col v-for="f in features" :key="f.name" :xs="24" :sm="12" :md="8">
          <div class="feat-item">
            <el-icon :size="18" style="color:#2D6BFF"><CircleCheckFilled /></el-icon>
            <div>
              <div class="feat-name">{{ f.name }}</div>
              <div class="feat-desc">{{ f.desc }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { DataAnalysis, MagicStick, Refresh, Platform, Connection, CircleCheckFilled } from '@element-plus/icons-vue'

const modelRows = [
  { metric: 'R² 决定系数', value: '0.9323', desc: '拟合优度，越接近 1 越好' },
  { metric: 'RMSE 均方根误差', value: '1.403 万', desc: '平均预测偏差幅度' },
  { metric: 'MAE 平均绝对误差', value: '1.0135 万', desc: '预测价与真实价平均差' },
  { metric: 'MAPE 平均绝对百分比', value: '20.51%', desc: '相对误差比例' },
  { metric: '训练 / 测试样本', value: '400,000 / 100,000', desc: '8:2 随机划分' },
  { metric: '模型文件', value: 'rf_price_model.joblib', desc: '26 MB，生产加载' }
]

const features = [
  { name: '数据看板', desc: '全局统计 + 筛选联动 + 多维图表' },
  { name: '价格预测', desc: '随机森林预测 + SHAP 因子 + 市场对比' },
  { name: '模型分析', desc: '特征重要性 / 性能对比 / 异步重训' },
  { name: '车辆列表', desc: '百万级车辆数据分页检索' },
  { name: '预测历史', desc: '历史预测记录留存' },
  { name: '数据血缘', desc: 'ETL 全链路可视化追溯' }
]
</script>

<style scoped>
.intro-text {
  font-size: 14px;
  color: #4B5563;
  line-height: 1.9;
  padding: 4px 2px 16px;
}

.intro-highlights {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  border-top: 1px dashed #E5E7EB;
  padding-top: 16px;
}

.hl-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #F9FAFB;
  border-radius: 10px;
  padding: 14px;
  border: 1px solid #EEF1F6;
}

.hl-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.hl-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.hl-desc {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}

.repo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.repo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  background: #F9FAFB;
  border: 1px solid #EEF1F6;
  border-radius: 10px;
  padding: 12px 14px;
  transition: box-shadow 0.2s, transform 0.2s;
}

.repo-item:hover {
  box-shadow: 0 6px 18px rgba(15, 30, 58, 0.1);
  transform: translateY(-2px);
}

.repo-icon {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.repo-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.repo-desc {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}

.deploy-note {
  display: flex;
  align-items: center;
  margin-top: 14px;
  font-size: 12.5px;
  color: #4B5563;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 8px;
  padding: 10px 12px;
}

.deploy-note code {
  background: #fff;
  border: 1px solid #D1FAE5;
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 12px;
  color: #15803D;
}

.feat-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #F9FAFB;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  border: 1px solid #EEF1F6;
}

.feat-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
}

.feat-desc {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}
</style>
