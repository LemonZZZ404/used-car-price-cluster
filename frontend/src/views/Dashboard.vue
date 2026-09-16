<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #2D6BFF, #5B8CFF)">
            <el-icon><Car /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(summary.total_cars) }}</div>
            <div class="stat-label">车辆总数</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #22C55E, #4ADE80)">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_brands || 0 }}</div>
            <div class="stat-label">品牌数量</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #F59E0B, #FBBF24)">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatPrice(summary.avg_price) }}<span class="stat-unit">万</span></div>
            <div class="stat-label">平均售价</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #EF4444, #F87171)">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ summary.total_predictions || 0 }}</div>
            <div class="stat-label">预测次数</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :sm="24" :md="12">
        <div class="card">
          <div class="card-title">品牌均价 Top 10</div>
          <div ref="brandChartRef" v-loading="loading" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <div class="card">
          <div class="card-title">车龄与价格关系</div>
          <div ref="ageChartRef" v-loading="loading" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :sm="24" :md="12">
        <div class="card">
          <div class="card-title">价格分布</div>
          <div ref="priceDistChartRef" v-loading="loading" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <div class="card">
          <div class="card-title">最近预测记录</div>
          <el-table :data="summary.latest_predictions || []" size="small" stripe>
            <el-table-column prop="brand" label="品牌" width="80" />
            <el-table-column prop="age" label="车龄" width="60">
              <template #default="{ row }">{{ row.age }}年</template>
            </el-table-column>
            <el-table-column prop="mileage" label="里程" width="80">
              <template #default="{ row }">{{ row.mileage }}万</template>
            </el-table-column>
            <el-table-column prop="predicted_price" label="预测价格" width="100">
              <template #default="{ row }">
                <span style="color:#EF4444;font-weight:600">{{ row.predicted_price }}万</span>
              </template>
            </el-table-column>
            <el-table-column prop="model_type" label="模型" width="100" />
            <el-table-column prop="create_time" label="时间" min-width="140" />
          </el-table>
          <el-empty v-if="!summary.latest_predictions || summary.latest_predictions.length === 0"
                    description="暂无预测记录" :image-size="80" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getBrandPriceTop10, getAgePriceChart, getPriceDistributionChart } from '@/api'

const summary = ref({})
const loading = ref(false)
const brandChartRef = ref(null)
const ageChartRef = ref(null)
const priceDistChartRef = ref(null)

let brandChart = null
let ageChart = null
let priceDistChart = null

// 统一图表色板
const CHART_COLORS = ['#2D6BFF', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#EC4899', '#84CC16']

// 数字格式化：999999 -> 999,999
const formatNumber = (n) => {
  if (n === undefined || n === null) return 0
  return Number(n).toLocaleString('zh-CN')
}

// 价格格式化
const formatPrice = (p) => {
  if (p === undefined || p === null) return '0.00'
  return Number(p).toFixed(2)
}

const initCharts = () => {
  if (brandChartRef.value) brandChart = echarts.init(brandChartRef.value)
  if (ageChartRef.value) ageChart = echarts.init(ageChartRef.value)
  if (priceDistChartRef.value) priceDistChart = echarts.init(priceDistChartRef.value)
}

const loadDashboard = async () => {
  try {
    const res = await getDashboardSummary()
    if (res.code === 200) summary.value = res.data
  } catch (e) {
    console.error('加载看板数据失败', e)
  }
}

const loadBrandChart = async () => {
  try {
    loading.value = true
    const res = await getBrandPriceTop10()
    if (!brandChart) return
    brandChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['平均售价', '车辆数量'], top: 0, textStyle: { color: '#4B5563' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: res.xAxis || [],
        axisLabel: { rotate: 30, color: '#6B7280' },
        axisLine: { lineStyle: { color: '#E5E7EB' } }
      },
      yAxis: [
        {
          type: 'value', name: '售价(万)',
          nameTextStyle: { color: '#9CA3AF' },
          axisLabel: { color: '#6B7280' },
          splitLine: { lineStyle: { color: '#F3F4F6' } }
        },
        {
          type: 'value', name: '数量',
          nameTextStyle: { color: '#9CA3AF' },
          axisLabel: { color: '#6B7280' },
          splitLine: { show: false }
        }
      ],
      series: (res.series || []).map((s, i) => ({
        ...s,
        barMaxWidth: 24,
        itemStyle: {
          borderRadius: i === 0 ? [4, 4, 0, 0] : [0, 0, 4, 4],
          color: i === 0 ? '#2D6BFF' : '#B9D1FF'
        }
      }))
    })
  } catch (e) {
    // 使用模拟数据
    brandChart?.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['保时捷', '奔驰', '宝马', '奥迪', '雷克萨斯', '沃尔沃', '特斯拉', '大众', '丰田', '本田'] },
      yAxis: { type: 'value', name: '售价(万)' },
      series: [{ type: 'bar', data: [85, 42, 40, 36, 35, 32, 28, 16, 16, 15], itemStyle: { color: '#2D6BFF', borderRadius: [4, 4, 0, 0] } }]
    })
  } finally {
    loading.value = false
  }
}

const loadAgeChart = async () => {
  try {
    loading.value = true
    const res = await getAgePriceChart()
    if (!ageChart) return
    ageChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis' },
      legend: { data: ['平均售价', '车辆数量'], top: 0, textStyle: { color: '#4B5563' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: res.xAxis || [],
        axisLabel: { color: '#6B7280' },
        axisLine: { lineStyle: { color: '#E5E7EB' } }
      },
      yAxis: [
        {
          type: 'value', name: '售价(万)',
          nameTextStyle: { color: '#9CA3AF' },
          axisLabel: { color: '#6B7280' },
          splitLine: { lineStyle: { color: '#F3F4F6' } }
        },
        {
          type: 'value', name: '数量',
          nameTextStyle: { color: '#9CA3AF' },
          axisLabel: { color: '#6B7280' },
          splitLine: { show: false }
        }
      ],
      series: (res.series || []).map((s, i) => ({
        ...s,
        smooth: true,
        symbolSize: 6,
        itemStyle: { color: i === 0 ? '#2D6BFF' : '#F59E0B' },
        lineStyle: { width: 3 },
        areaStyle: i === 0 ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(45,107,255,0.25)' },
            { offset: 1, color: 'rgba(45,107,255,0.02)' }
          ])
        } : undefined
      }))
    })
  } catch (e) {
    ageChart?.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['0年','1年','2年','3年','4年','5年','6年','7年','8年','10年','12年','15年'] },
      yAxis: { type: 'value', name: '售价(万)' },
      series: [{
        type: 'line', smooth: true, data: [22, 19, 16, 14, 12, 10, 8.5, 7.5, 6.5, 5, 4, 3],
        itemStyle: { color: '#2D6BFF' },
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(45,107,255,0.25)' },
            { offset: 1, color: 'rgba(45,107,255,0.02)' }
          ])
        }
      }]
    })
  } finally {
    loading.value = false
  }
}

const loadPriceDistChart = async () => {
  try {
    loading.value = true
    const res = await getPriceDistributionChart()
    if (!priceDistChart) return
    priceDistChart.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'item', formatter: '{b}: {c}辆 ({d}%)' },
      legend: { orient: 'vertical', left: 'left', textStyle: { color: '#4B5563' } },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['55%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 18, fontWeight: 'bold', color: '#1F2937' } },
        labelLine: { show: false },
        data: res.pie_data || []
      }]
    })
  } catch (e) {
    priceDistChart?.setOption({
      color: CHART_COLORS,
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'], center: ['55%', '50%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        data: [
          { value: 3200, name: '0-5万' }, { value: 5800, name: '5-10万' },
          { value: 4500, name: '10-15万' }, { value: 3000, name: '15-20万' },
          { value: 2000, name: '20-30万' }, { value: 1000, name: '30-50万' },
          { value: 500, name: '50万以上' }
        ]
      }]
    })
  } finally {
    loading.value = false
  }
}

const handleResize = () => {
  brandChart?.resize()
  ageChart?.resize()
  priceDistChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await Promise.all([loadDashboard(), loadBrandChart(), loadAgeChart(), loadPriceDistChart()])
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  brandChart?.dispose()
  ageChart?.dispose()
  priceDistChart?.dispose()
})
</script>

<style scoped>
.dashboard { padding: 0; }
.stat-row { margin-bottom: 20px; }
.stat-row .el-col { margin-bottom: 12px; }
.chart-row { margin-bottom: 20px; }
.chart-row .el-col { margin-bottom: 12px; }

.stat-unit {
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 4px;
}
</style>
