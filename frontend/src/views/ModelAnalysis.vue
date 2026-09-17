<template>
  <div class="model-analysis">
    <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
      <!-- ============ Tab 1 模型总览 ============ -->
      <el-tab-pane label="模型总览" name="overview">
        <!-- 模型重训控制台 -->
        <div class="card train-console" v-if="userStore.isAdmin">
          <div class="card-title" style="margin-bottom:14px">
            <span>模型重训控制台</span>
            <el-tag type="warning" effect="light" size="small" round>Celery 异步任务</el-tag>
          </div>
          <div class="train-body">
            <div class="train-left">
              <el-button
                type="primary"
                size="large"
                :loading="trainState.status === 'running'"
                :disabled="trainState.status === 'running'"
                @click="handleTrain"
                style="background: linear-gradient(90deg, #F59E0B, #FBBF24); border:none; color:#fff"
              >
                <el-icon style="margin-right:6px"><Refresh /></el-icon>
                {{ trainState.status === 'running' ? '训练中...' : '一键重训模型' }}
              </el-button>
              <span class="train-hint">基于 {{ (sklearn.train_size ? Number(sklearn.train_size).toLocaleString() : '—') }} 条样本，异步执行全量重训（约 1 分钟）</span>
            </div>
            <div class="train-progress" v-if="trainState.status === 'running' || (trainState.status === 'success' && trainState.progress > 0)">
              <div class="train-progress-head">
                <span class="train-msg">{{ trainState.message || '准备中...' }}</span>
                <span class="train-pct">{{ trainState.progress || 0 }}%</span>
              </div>
              <el-progress
                :percentage="trainState.progress || 0"
                :stroke-width="10"
                :color="trainState.status === 'error' ? '#EF4444' : 'linear-gradient(90deg, #F59E0B, #FBBF24)'"
                :status="trainState.status === 'error' ? 'exception' : (trainState.status === 'success' ? 'success' : '')"
              />
            </div>
            <el-alert
              v-if="trainState.status === 'success' && trainState.metrics && trainState.metrics.r2"
              type="success"
              :closable="false"
              style="margin-top:14px"
              show-icon
            >
              <template #title>
                <div class="train-success">
                  <span>训练完成：R² = {{ trainState.metrics.r2 }}，RMSE = {{ trainState.metrics.rmse }} 万</span>
                  <span class="train-success-time">（{{ trainState.updated_at }}）</span>
                </div>
              </template>
            </el-alert>
            <el-alert
              v-if="trainState.status === 'error'"
              type="error"
              :closable="false"
              style="margin-top:14px"
              show-icon
              :title="trainState.message"
            />
          </div>
        </div>

        <!-- 模型对比指标卡片 -->
        <el-row :gutter="20" class="metric-row">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #2D6BFF, #5B8CFF)">
                <el-icon><Odometer /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatMetric(sklearn.r2) }}</div>
                <div class="stat-label">R² 决定系数</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #22C55E, #4ADE80)">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatMetric(sklearn.rmse) }}<span class="stat-unit">万</span></div>
                <div class="stat-label">RMSE 均方根误差</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #F59E0B, #FBBF24)">
                <el-icon><Aim /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatMetric(sklearn.mae) }}<span class="stat-unit">万</span></div>
                <div class="stat-label">MAE 平均绝对误差</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-card">
              <div class="stat-icon" style="background: linear-gradient(135deg, #EF4444, #F87171)">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatNumber(sklearn.train_size) }}</div>
                <div class="stat-label">训练样本数</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 模型文件与配置 -->
        <div class="card">
          <div class="card-title">
            <span>模型文件与配置</span>
            <el-tag type="success" effect="light" size="small" round>生产加载</el-tag>
          </div>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="模型文件">rf_price_model.joblib</el-descriptions-item>
            <el-descriptions-item label="模型类型">{{ sklearn.model || 'Scikit-learn RandomForestRegressor' }}</el-descriptions-item>
            <el-descriptions-item label="文件大小">26 MB</el-descriptions-item>
            <el-descriptions-item label="特征维度">{{ featureImportance.length }} 个特征</el-descriptions-item>
            <el-descriptions-item label="训练 / 测试样本">
              {{ sklearn.train_size ? Number(sklearn.train_size).toLocaleString() : '-' }} / {{ sklearn.test_size ? Number(sklearn.test_size).toLocaleString() : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="树数量 / 最大深度">
              {{ sklearn.n_estimators ?? '-' }} / {{ sklearn.max_depth ?? '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="训练耗时">
              {{ sklearn.train_time_seconds ? sklearn.train_time_seconds + ' 秒' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="最近训练时间">
              <span style="color:#2D6BFF;font-weight:600">{{ sklearn.train_time || '-' }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-tab-pane>

      <!-- ============ Tab 2 特征分析 ============ -->
      <el-tab-pane label="特征分析" name="features">
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <div class="card">
              <div class="card-title">
                <span>特征重要性 Top 12</span>
                <el-tag type="primary" effect="light" size="small" round>Scikit-learn 随机森林</el-tag>
              </div>
              <div ref="importanceChartRef" v-loading="loading" class="chart-container-lg"></div>
            </div>
          </el-col>
          <el-col :xs="24" :md="12">
            <div class="card">
              <div class="card-title">
                <span>特征贡献解读</span>
                <el-tag type="info" effect="light" size="small" round>模型可解释性</el-tag>
              </div>
              <div class="insight-list">
                <div v-if="featureRows.length >= 3" class="insight-item">
                  <div class="insight-tag">TOP 1</div>
                  <div class="insight-text"><b>{{ featureRows[0].label }}</b> 贡献 {{ featureRows[0].pct }}%，是价格最主要决定因素</div>
                </div>
                <div v-if="featureRows.length >= 3" class="insight-item">
                  <div class="insight-tag" style="background:#E0F2FE;color:#0369A1">TOP 2</div>
                  <div class="insight-text"><b>{{ featureRows[1].label }}</b> 贡献 {{ featureRows[1].pct }}%，与 {{ featureRows[0].label }} 合计 {{ (featureRows[0].pct*1 + featureRows[1].pct*1).toFixed(2) }}%</div>
                </div>
                <div v-if="featureRows.length >= 3" class="insight-item">
                  <div class="insight-tag" style="background:#DCFCE7;color:#15803D">TOP 3</div>
                  <div class="insight-text"><b>{{ featureRows[2].label }}</b> 贡献 {{ featureRows[2].pct }}%，前 3 项累计 {{ (featureRows[0].pct*1 + featureRows[1].pct*1 + featureRows[2].pct*1).toFixed(2) }}%</div>
                </div>
                <div v-if="featureRows.length" class="insight-item">
                  <div class="insight-tag" style="background:#F3F4F6;color:#4B5563">品牌</div>
                  <div class="insight-text">品牌哑变量合计 {{ brandTotalPct }}%，反映品牌溢价对二手车价的影响</div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <!-- 特征重要性完整明细表 -->
        <div class="card" style="margin-top:20px">
          <div class="card-title">
            <span>特征重要性明细（全量 {{ featureRows.length }} 个特征）</span>
            <el-tag type="primary" effect="plain" size="small" round>按贡献排序</el-tag>
          </div>
          <el-table :data="featureRows" v-loading="loading" stripe border size="small">
            <el-table-column prop="rank" label="排名" width="70" align="center">
              <template #default="{ row }">
                <span v-if="row.rank <= 3" class="rank-badge">{{ row.rank }}</span>
                <span v-else style="color:#9CA3AF">{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="label" label="特征" min-width="140">
              <template #default="{ row }">
                <span style="font-weight:600">{{ row.label }}</span>
                <span style="color:#C0C4CC;font-size:12px;margin-left:6px">{{ row.feature }}</span>
              </template>
            </el-table-column>
            <el-table-column label="重要性" width="220">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.round(row.pct)"
                  :stroke-width="8"
                  :show-text="false"
                  :color="row.rank <= 3 ? 'linear-gradient(90deg,#5B8CFF,#2D6BFF)' : '#93C5FD'"
                />
              </template>
            </el-table-column>
            <el-table-column prop="pct" label="贡献占比" width="100" align="right">
              <template #default="{ row }">
                <span style="font-weight:600;color:#2D6BFF">{{ row.pct }}%</span>
              </template>
            </el-table-column>
            <el-table-column prop="cum" label="累计贡献" width="110" align="right">
              <template #default="{ row }">
                <span style="color:#6B7280">{{ row.cum }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- ============ Tab 3 性能对比 ============ -->
      <el-tab-pane label="性能对比" name="compare">
        <el-row :gutter="20">
          <el-col :xs="24" :md="10">
            <div class="card">
              <div class="card-title">模型性能对比</div>
              <div ref="compareChartRef" v-loading="loading" class="chart-container-lg"></div>
            </div>
          </el-col>
          <el-col :xs="24" :md="14">
            <div class="card">
              <div class="card-title">
                <span>性能指标明细</span>
                <el-tag type="success" effect="light" size="small" round>Scikit-learn 当前模型</el-tag>
              </div>
              <el-table :data="compareRows" v-loading="loading" stripe border size="default">
                <el-table-column prop="group" label="分组" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.groupType" size="small" effect="plain">{{ row.group }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="metric" label="指标" min-width="130" />
                <el-table-column prop="sklearn" label="Scikit-learn" width="150" />
                <el-table-column prop="spark" label="Spark MLlib" width="150" />
                <el-table-column label="评分" width="90">
                  <template #default="{ row }">
                    <el-tag v-if="row.grade" :type="row.gradeType" size="small" effect="dark" round>{{ row.grade }}</el-tag>
                    <span v-else style="color:#C0C4CC">—</span>
                  </template>
                </el-table-column>
                <el-table-column label="说明" min-width="160">
                  <template #default="{ row }">
                    <span style="color:#6B7280;font-size:12.5px">{{ row.desc }}</span>
                  </template>
                </el-table-column>
              </el-table>
              <el-alert
                v-if="compareNote"
                type="info"
                :closable="false"
                style="margin-top:16px"
                :title="compareNote"
              />
            </div>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ============ Tab 4 数据血缘 ============ -->
      <el-tab-pane label="数据血缘" name="lineage">
        <div class="card">
          <div class="card-title">
            <span>数据血缘 · ETL 链路</span>
            <el-tag type="warning" effect="light" size="small" round>三机集群实测</el-tag>
          </div>
          <el-table :data="lineageRows" size="small" stripe border>
            <el-table-column prop="stage" label="阶段" width="110">
              <template #default="{ row }">
                <span style="font-weight:600">{{ row.stage }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="engine" label="引擎/组件" width="140" />
            <el-table-column prop="count" label="数据量" width="130">
              <template #default="{ row }">
                <span v-if="row.count" style="font-weight:600;color:#2D6BFF">{{ row.count }}</span>
                <span v-else style="color:#C0C4CC">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="desc" label="说明" min-width="200">
              <template #default="{ row }">
                <span style="color:#6B7280;font-size:12.5px">{{ row.desc }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="lineage-flow">
            <el-tag size="small" effect="plain" type="primary">MySQL</el-tag>
            <span class="flow-arrow">Sqoop →</span>
            <el-tag size="small" effect="plain" type="primary">ODS</el-tag>
            <span class="flow-arrow">Hive ETL →</span>
            <el-tag size="small" effect="plain" type="primary">DWD</el-tag>
            <span class="flow-arrow">Spark SQL →</span>
            <el-tag size="small" effect="plain" type="primary">ADS</el-tag>
            <span class="flow-arrow">→</span>
            <el-tag size="small" effect="plain" type="primary">Django/Vue</el-tag>
          </div>
          <div class="lineage-note">
            <el-icon style="margin-right:6px;color:#F59E0B"><InfoFilled /></el-icon>
            <span>数据从 MySQL 业务库经 Sqoop 入仓，Hive 清洗建模（ODS→DWD），Spark SQL 聚合出 ADS 统计结果，最终由 Django API 供前端看板与预测使用。</span>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Odometer, TrendCharts, Aim, Cpu, Refresh, InfoFilled } from '@element-plus/icons-vue'
import { getModelAnalysis, trainStart, trainStatus } from '@/api'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const activeTab = ref('overview')
const loading = ref(false)
const data = ref({})
const importanceChartRef = ref(null)
const compareChartRef = ref(null)
let importanceChart = null
let compareChart = null
let trainPollTimer = null
const trainState = ref({ status: 'idle', progress: 0, message: '', metrics: {} })

const sklearn = computed(() => data.value.sklearn_metrics || {})
const spark = computed(() => data.value.spark_metrics || {})
const featureImportance = computed(() => data.value.feature_importance || [])

// ---------- 特征分析 ----------
const featureLabel = (f) => {
  if (f.startsWith('brand_')) return '品牌-' + f.slice(6)
  const map = { original_price: '新车价格', age: '车龄', mileage: '行驶里程' }
  return map[f] || f
}

const featureRows = computed(() => {
  const sorted = [...featureImportance.value].sort((a, b) => b.importance - a.importance)
  let acc = 0
  return sorted.map((item, idx) => {
    acc += item.importance
    return {
      rank: idx + 1,
      feature: item.feature,
      label: featureLabel(item.feature),
      importance: item.importance,
      pct: (item.importance * 100).toFixed(2),
      cum: (acc * 100).toFixed(2)
    }
  })
})

const brandTotalPct = computed(() => {
  const total = featureRows.value
    .filter(r => r.feature.startsWith('brand_'))
    .reduce((s, r) => s + Number(r.pct), 0)
  return total.toFixed(2)
})

// ---------- 性能明细 ----------
const gradeOf = (score, type) => {
  if (score === undefined || score === null) return null
  if (type === 'r2') {
    if (score >= 0.9) return { text: '优秀', type: 'success' }
    if (score >= 0.8) return { text: '良好', type: 'warning' }
    return { text: '待提升', type: 'danger' }
  }
  if (score <= 2) return { text: '优秀', type: 'success' }
  if (score <= 5) return { text: '良好', type: 'warning' }
  return { text: '待提升', type: 'danger' }
}

const compareRows = computed(() => {
  const s = sklearn.value
  const sp = spark.value
  const g1 = gradeOf(s.r2, 'r2')
  const g2 = gradeOf(s.rmse)
  const g3 = gradeOf(s.mae)
  return [
    { group: '性能', groupType: 'primary', metric: 'R² 决定系数', sklearn: s.r2?.toFixed(4) ?? '-', spark: sp.r2?.toFixed(4) ?? '-', grade: g1?.text, gradeType: g1?.type, desc: '越接近 1 拟合越好' },
    { group: '性能', groupType: 'primary', metric: 'RMSE (万元)', sklearn: s.rmse?.toFixed(4) ?? '-', spark: sp.rmse?.toFixed(4) ?? '-', grade: g2?.text, gradeType: g2?.type, desc: '均方根误差，越小越好' },
    { group: '性能', groupType: 'primary', metric: 'MAE (万元)', sklearn: s.mae?.toFixed(4) ?? '-', spark: sp.mae?.toFixed(4) ?? '-', grade: g3?.text, gradeType: g3?.type, desc: '平均绝对误差，越小越好' },
    { group: '性能', groupType: 'primary', metric: 'MAPE (%)', sklearn: s.mape?.toFixed(2) ?? '-', spark: '-', grade: null, gradeType: null, desc: '平均绝对百分比误差' },
    { group: '数据', groupType: 'success', metric: '训练样本数', sklearn: s.train_size ? Number(s.train_size).toLocaleString() : '-', spark: sp.train_size ? Number(sp.train_size).toLocaleString() : '-', grade: null, gradeType: null, desc: '模型训练使用的样本量' },
    { group: '数据', groupType: 'success', metric: '测试样本数', sklearn: s.test_size ? Number(s.test_size).toLocaleString() : '-', spark: sp.test_size ? Number(sp.test_size).toLocaleString() : '-', grade: null, gradeType: null, desc: '模型评估使用的样本量' },
    { group: '配置', groupType: 'warning', metric: '树数量', sklearn: s.n_estimators ?? '-', spark: sp.num_trees ?? '-', grade: null, gradeType: null, desc: '随机森林中决策树数量' },
    { group: '配置', groupType: 'warning', metric: '最大深度', sklearn: s.max_depth ?? '-', spark: sp.max_depth ?? '-', grade: null, gradeType: null, desc: '决策树最大深度' },
    { group: '配置', groupType: 'warning', metric: '训练耗时', sklearn: s.train_time_seconds ? `${s.train_time_seconds}s` : '-', spark: '-', grade: null, gradeType: null, desc: '训练花费时间' },
    { group: '配置', groupType: 'warning', metric: '训练时间', sklearn: s.train_time ?? '-', spark: sp.train_time ?? '-', grade: null, gradeType: null, desc: '模型训练完成时间' }
  ]
})

const compareNote = computed(() => {
  const s = sklearn.value
  const sp = spark.value
  if (s && sp && s.train_size && sp.train_size && s.train_size > sp.train_size) {
    return `说明：Scikit-learn 使用 ${Number(s.train_size).toLocaleString()} 条样本训练（在线预测），Spark MLlib 为早期 ${Number(sp.train_size).toLocaleString()} 条小样本对比实验（离线训练演示）。两者体现"单机 vs 分布式"两种技术路线。`
  }
  return ''
})

// ---------- 数据血缘 ----------
const lineageRows = [
  { stage: '业务库', engine: 'MySQL', count: '999,999 条', desc: 'car_info 车辆信息表（18 列）' },
  { stage: '采集', engine: 'Sqoop', count: '999,998 条', desc: '14 列精确导入 HDFS' },
  { stage: 'ODS', engine: 'Hive', count: '999,998 条', desc: '原始数据入仓 ods_car_info' },
  { stage: 'DWD', engine: 'Hive MR ETL', count: '999,998 条', desc: '清洗去重 dwd_car_info (dt=20240101)' },
  { stage: 'ADS', engine: 'Spark SQL', count: '28 行', desc: '品牌均价 stat_brand_price' },
  { stage: 'ADS', engine: 'Spark SQL', count: '21 行', desc: '车龄价格 stat_age_price' },
  { stage: 'ADS', engine: 'Spark SQL', count: '6 行', desc: '价格分布 stat_price_distribution' },
  { stage: '应用层', engine: 'Django/Vue', count: '—', desc: '看板 / 预测 / 模型分析' }
]

const formatNumber = (n) => {
  if (n === undefined || n === null) return '-'
  return Number(n).toLocaleString('zh-CN')
}

const formatMetric = (v) => {
  if (v === undefined || v === null) return '-'
  return Number(v).toFixed(4)
}

// ---------- 图表 ----------
const renderImportanceChart = () => {
  if (!importanceChartRef.value) return
  if (!importanceChart) importanceChart = echarts.init(importanceChartRef.value)
  const items = [...featureImportance.value].sort((a, b) => b.importance - a.importance).slice(0, 12).reverse()
  importanceChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${featureLabel(p.name)}<br/>重要性：${(p.value * 100).toFixed(2)}%`
      }
    },
    grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#6B7280', formatter: (v) => (v * 100).toFixed(0) + '%' },
      splitLine: { lineStyle: { color: '#F3F4F6' } }
    },
    yAxis: {
      type: 'category',
      data: items.map(i => featureLabel(i.feature)),
      axisLabel: { color: '#4B5563' },
      axisLine: { lineStyle: { color: '#E5E7EB' } }
    },
    series: [{
      type: 'bar',
      data: items.map(i => i.importance),
      barMaxWidth: 18,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#5B8CFF' },
          { offset: 1, color: '#2D6BFF' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: (p) => (p.value * 100).toFixed(1) + '%',
        color: '#4B5563',
        fontSize: 12
      }
    }]
  })
  importanceChart.resize()
}

const renderCompareChart = () => {
  if (!compareChartRef.value) return
  if (!compareChart) compareChart = echarts.init(compareChartRef.value)
  const s = sklearn.value
  const sp = spark.value
  if (!s || !sp) return

  compareChart.setOption({
    tooltip: {},
    legend: { data: ['Scikit-learn', 'Spark MLlib'], top: 0, textStyle: { color: '#4B5563' } },
    radar: {
      indicator: [
        { name: 'R²', max: 1 },
        { name: 'RMSE', max: 10 },
        { name: 'MAE', max: 10 }
      ],
      radius: '65%',
      axisName: { color: '#4B5563' },
      splitLine: { lineStyle: { color: '#E5E7EB' } },
      splitArea: { areaStyle: { color: ['#F9FAFB', '#F3F4F6'] } },
      axisLine: { lineStyle: { color: '#E5E7EB' } }
    },
    series: [{
      type: 'radar',
      data: [
        {
          name: 'Scikit-learn',
          value: [s.r2 ?? 0, s.rmse ?? 0, s.mae ?? 0],
          areaStyle: { color: 'rgba(45,107,255,0.2)' },
          lineStyle: { color: '#2D6BFF', width: 2 },
          itemStyle: { color: '#2D6BFF' }
        },
        {
          name: 'Spark MLlib',
          value: [sp.r2 ?? 0, sp.rmse ?? 0, sp.mae ?? 0],
          areaStyle: { color: 'rgba(34,197,94,0.15)' },
          lineStyle: { color: '#22C55E', width: 2 },
          itemStyle: { color: '#22C55E' }
        }
      ]
    }]
  })
  compareChart.resize()
}

// Tab 切换：目标 tab 内的图表需要等 DOM 可见后再 init/render
const handleTabChange = () => {
  nextTick(() => {
    if (activeTab.value === 'features') renderImportanceChart()
    if (activeTab.value === 'compare') renderCompareChart()
  })
}

const handleTrain = async () => {
  try {
    const res = await trainStart()
    if (res.code === 200) {
      ElMessage.success('训练任务已提交，正在后台异步执行')
      pollTrainStatus()
    } else {
      ElMessage.warning(res.message || '训练任务启动失败')
      if (res.code === 400) pollTrainStatus()
    }
  } catch (e) {
    ElMessage.error('提交训练任务失败，请确认后端与 Celery 服务正常')
  }
}

const pollTrainStatus = async () => {
  clearInterval(trainPollTimer)
  trainPollTimer = setInterval(async () => {
    try {
      const res = await trainStatus()
      if (res.code === 200) {
        trainState.value = res.data
        if (res.data.status === 'success' || res.data.status === 'error') {
          clearInterval(trainPollTimer)
          if (res.data.status === 'success') {
            ElMessage.success('模型训练完成！')
            await loadData()
          } else {
            ElMessage.error('模型训练失败')
          }
        }
      }
    } catch (e) {
      clearInterval(trainPollTimer)
    }
  }, 3000)
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getModelAnalysis()
    if (res.code === 200) {
      data.value = res.data
      nextTick(() => {
        if (activeTab.value === 'features') renderImportanceChart()
        if (activeTab.value === 'compare') renderCompareChart()
      })
    }
  } catch (e) {
    console.error('加载模型分析数据失败', e)
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  importanceChart?.resize()
  compareChart?.resize()
}

onMounted(async () => {
  await nextTick()
  loadData()
  try {
    const res = await trainStatus()
    if (res.code === 200) trainState.value = res.data
    if (res.data.status === 'running') pollTrainStatus()
  } catch (e) { /* 忽略 */ }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(trainPollTimer)
  window.removeEventListener('resize', handleResize)
  importanceChart?.dispose()
  compareChart?.dispose()
})
</script>

<style scoped>
.metric-row { margin-bottom: 20px; }
.metric-row .el-col { margin-bottom: 12px; }
.stat-unit {
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 4px;
}

.train-console {
  margin-bottom: 20px;
  background: linear-gradient(180deg, #FFFBEB 0%, #FFFFFF 60%);
  border: 1px solid #FDE68A;
}

.train-body { padding: 4px 2px; }

.train-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.train-hint {
  font-size: 13px;
  color: #9CA3AF;
}

.train-progress {
  margin-top: 16px;
}

.train-progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.train-msg {
  font-size: 13px;
  color: var(--text-primary);
}

.train-pct {
  font-size: 13px;
  font-weight: 600;
  color: #F59E0B;
}

.train-success {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.train-success-time {
  font-weight: 400;
  color: #9CA3AF;
  font-size: 12px;
}

.lineage-flow {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px 12px;
  background: #F9FAFB;
  border-radius: 8px;
  border: 1px dashed #E5E7EB;
}

.flow-arrow {
  color: #9CA3AF;
  font-size: 12px;
}

.lineage-note {
  margin-top: 14px;
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 13px;
  color: #6B7280;
  line-height: 1.6;
}

.insight-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: #F9FAFB;
  border-radius: 8px;
  border-left: 3px solid #2D6BFF;
}

.insight-tag {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: #DBEAFE;
  color: #1D4ED8;
}

.insight-text {
  font-size: 13px;
  color: #4B5563;
  line-height: 1.6;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}
</style>
