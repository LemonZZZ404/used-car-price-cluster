<template>
  <div>
    <!-- 数据链路总览 -->
    <div class="card" style="margin-bottom:20px">
      <div class="card-title">
        <span>数据链路总览</span>
        <el-tag type="warning" effect="light" size="small" round>MySQL → Hive → Spark → 前端</el-tag>
      </div>
      <div class="pipeline">
        <template v-for="(s, i) in pipeline" :key="s.name">
          <div class="pipe-node">
            <div class="pipe-icon" :style="{ background: s.color }">
              <el-icon :size="22"><component :is="s.icon" /></el-icon>
            </div>
            <div class="pipe-name">{{ s.name }}</div>
            <div class="pipe-engine">{{ s.engine }}</div>
            <div class="pipe-count" :class="{ dim: !s.count }">{{ s.count || '—' }}</div>
          </div>
          <div v-if="i < pipeline.length - 1" class="pipe-arrow">
            <el-icon :size="18"><Right /></el-icon>
          </div>
        </template>
      </div>
      <div class="pipeline-note">
        <el-icon style="margin-right:6px;color:#2D6BFF"><InfoFilled /></el-icon>
        <span>数据从 MySQL 业务库出发，经 Sqoop 批量采集进入 HDFS，由 Hive 分层建模（ODS 原始层 → DWD 清洗层），Spark SQL 完成聚合分析产出 ADS 结果表，最终 Django API 供前端看板与预测使用。</span>
      </div>
    </div>

    <!-- ETL 明细 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="14">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title">
            <span>ETL 分层明细</span>
            <el-tag type="primary" effect="light" size="small" round>三机集群实测</el-tag>
          </div>
          <el-table :data="lineageRows" size="small" stripe border>
            <el-table-column prop="stage" label="分层" width="100">
              <template #default="{ row }">
                <el-tag :type="row.tagType" size="small" effect="dark">{{ row.stage }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="engine" label="引擎/组件" width="130" />
            <el-table-column prop="count" label="数据量" width="120">
              <template #default="{ row }">
                <span v-if="row.count" style="font-weight:600;color:#2D6BFF">{{ row.count }}</span>
                <span v-else style="color:#C0C4CC">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="table" label="表 / 结果" min-width="150" />
            <el-table-column prop="desc" label="说明" min-width="160">
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
            <span>数据规模</span>
            <el-tag type="success" effect="light" size="small" round>百万级</el-tag>
          </div>
          <div class="scale-list">
            <div class="scale-item">
              <div class="scale-num" style="color:#2D6BFF">999,999</div>
              <div class="scale-label">MySQL 业务数据（条）</div>
            </div>
            <div class="scale-item">
              <div class="scale-num" style="color:#7C3AED">999,998</div>
              <div class="scale-label">Hive DWD 清洗后（条）</div>
            </div>
            <div class="scale-item">
              <div class="scale-num" style="color:#22C55E">3 张</div>
              <div class="scale-label">ADS 统计结果表</div>
            </div>
            <div class="scale-item">
              <div class="scale-num" style="color:#F59E0B">15 个</div>
              <div class="scale-label">模型特征维度</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 三机集群架构 -->
    <div class="card">
      <div class="card-title">
        <span>三机分布式集群架构</span>
        <el-tag type="warning" effect="light" size="small" round>hadoop101 / 102 / 103</el-tag>
      </div>
      <el-row :gutter="20">
        <el-col v-for="node in nodes" :key="node.ip" :xs="24" :md="8">
          <div class="node-card" :class="{ master: node.role === 'Master' }">
            <div class="node-head">
              <div class="node-icon">
                <el-icon :size="20"><Platform /></el-icon>
              </div>
              <div>
                <div class="node-host">{{ node.host }}</div>
                <div class="node-ip">{{ node.ip }}</div>
              </div>
              <el-tag :type="node.role === 'Master' ? 'danger' : 'primary'" size="small" effect="dark" round>{{ node.role }}</el-tag>
            </div>
            <div class="node-svc">
              <div v-for="svc in node.services" :key="svc" class="svc-item">
                <span class="svc-dot"></span>{{ svc }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { Coin, Download, Box, Files, FolderOpened, Lightning, DataLine, Monitor, Right, InfoFilled, Platform } from '@element-plus/icons-vue'

const pipeline = [
  { name: '业务库', engine: 'MySQL', count: '999,999 条', icon: 'Coin', color: 'linear-gradient(135deg,#F59E0B,#FBBF24)' },
  { name: '数据采集', engine: 'Sqoop', count: '14 列精确导入', icon: 'Download', color: 'linear-gradient(135deg,#7C3AED,#A78BFA)' },
  { name: 'ODS 原始层', engine: 'Hive 建表', count: '999,998 条', icon: 'Box', color: 'linear-gradient(135deg,#0891B2,#22D3EE)' },
  { name: 'DWD 清洗层', engine: 'Hive MR ETL', count: '999,998 条', icon: 'FolderOpened', color: 'linear-gradient(135deg,#2D6BFF,#5B8CFF)' },
  { name: 'ADS 结果层', engine: 'Spark SQL', count: '28/21/6 行', icon: 'Lightning', color: 'linear-gradient(135deg,#22C55E,#4ADE80)' },
  { name: 'API 服务', engine: 'Django', count: 'RESTful', icon: 'Files', color: 'linear-gradient(135deg,#EF4444,#F87171)' },
  { name: '前端展示', engine: 'Vue3 + ECharts', count: '可视化', icon: 'Monitor', color: 'linear-gradient(135deg,#0F1E3A,#2D6BFF)' }
]

const lineageRows = [
  { stage: '业务库', tagType: 'warning', engine: 'MySQL', count: '999,999 条', table: 'car_info', desc: '18 列车辆信息，含价格/车龄/里程' },
  { stage: '采集', tagType: 'info', engine: 'Sqoop', count: '999,998 条', table: 'HDFS 文件', desc: '14 列精确查询导入' },
  { stage: 'ODS', tagType: 'primary', engine: 'Hive', count: '999,998 条', table: 'ods_car_info', desc: '原始数据入仓，保持源结构' },
  { stage: 'DWD', tagType: 'primary', engine: 'Hive MR', count: '999,998 条', table: 'dwd_car_info', desc: '清洗去重，dt=20240101 分区' },
  { stage: 'ADS', tagType: 'success', engine: 'Spark SQL', count: '28 行', table: 'stat_brand_price', desc: '品牌维度均价聚合' },
  { stage: 'ADS', tagType: 'success', engine: 'Spark SQL', count: '21 行', table: 'stat_age_price', desc: '车龄-价格趋势聚合' },
  { stage: 'ADS', tagType: 'success', engine: 'Spark SQL', count: '6 行', table: 'stat_price_distribution', desc: '价格区间分布聚合' },
  { stage: '应用层', tagType: 'danger', engine: 'Django/Vue', count: '—', table: 'REST API', desc: '看板 / 预测 / 模型分析' }
]

const nodes = [
  {
    host: 'hadoop101', ip: '192.168.249.101', role: 'Master',
    services: ['NameNode', 'JobHistoryServer', 'Hive Metastore (9083)', 'HiveServer2 (10000)', 'MySQL (3306)', 'Redis (6379)', 'Django (8000)', 'Nginx (80)', 'Celery 异步任务', 'ZooKeeper', 'Kafka']
  },
  {
    host: 'hadoop102', ip: '192.168.249.102', role: 'Worker',
    services: ['ResourceManager', 'NodeManager', 'ZooKeeper', 'Kafka']
  },
  {
    host: 'hadoop103', ip: '192.168.249.103', role: 'Worker',
    services: ['SecondaryNameNode', 'NodeManager', 'ZooKeeper', 'Kafka']
  }
]
</script>

<style scoped>
.pipeline {
  display: flex;
  align-items: stretch;
  gap: 6px;
  flex-wrap: wrap;
  padding: 8px 2px 16px;
}

.pipe-node {
  flex: 1;
  min-width: 110px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 14px 10px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.pipe-node:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(15, 30, 58, 0.1);
}

.pipe-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  margin: 0 auto 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 10px rgba(15, 30, 58, 0.15);
}

.pipe-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.pipe-engine {
  font-size: 12px;
  color: #6B7280;
  margin-top: 3px;
}

.pipe-count {
  font-size: 12px;
  font-weight: 600;
  color: #2D6BFF;
  margin-top: 5px;
}

.pipe-count.dim { color: #9CA3AF; }

.pipe-arrow {
  display: flex;
  align-items: center;
  color: #C0C4CC;
}

.pipeline-note {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 13px;
  color: #6B7280;
  line-height: 1.7;
  padding: 12px 14px;
  background: #F0F6FF;
  border-radius: 8px;
  border: 1px solid #D6E4FF;
}

.scale-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.scale-item {
  background: #F9FAFB;
  border-radius: 10px;
  padding: 16px 12px;
  text-align: center;
  border: 1px solid #EEF1F6;
}

.scale-num {
  font-size: 24px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.scale-label {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 6px;
}

.node-card {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 16px;
  height: 100%;
  transition: box-shadow 0.25s, transform 0.25s;
}

.node-card:hover {
  box-shadow: 0 8px 24px rgba(15, 30, 58, 0.1);
  transform: translateY(-2px);
}

.node-card.master {
  border-color: #FCA5A5;
  background: linear-gradient(180deg, #FEF2F2, #FFFFFF 50%);
}

.node-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #E5E7EB;
  margin-bottom: 12px;
}

.node-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.node-host {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.node-ip {
  font-size: 12px;
  color: #9CA3AF;
}

.node-svc {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.svc-item {
  font-size: 12px;
  color: #4B5563;
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 3px 8px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.svc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22C55E;
}
</style>
