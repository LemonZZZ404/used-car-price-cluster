<template>
  <div class="dashboard">
    <!-- 全局筛选栏 -->
    <div class="filter-bar">
      <el-form inline class="filter-form">
        <el-form-item label="品牌">
          <el-select v-model="filters.brand" placeholder="全部品牌" filterable clearable style="width:160px" @change="applyFilters">
            <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
          </el-select>
        </el-form-item>
        <el-form-item label="城市">
          <el-select v-model="filters.city" placeholder="全部城市" filterable clearable style="width:160px" @change="applyFilters">
            <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格区间">
          <el-select v-model="filters.price_range" placeholder="价格不限" clearable style="width:140px" @change="applyFilters">
            <el-option v-for="r in priceRanges" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
          <el-tag v-if="isFiltered" type="warning" effect="light" size="small" style="margin-left:8px">
            已按条件筛选，图表联动更新
          </el-tag>
        </el-form-item>
      </el-form>
    </div>

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
          <div class="card-title">
            品牌均价 Top 10
            <span class="card-sub">全局统计，底部可缩放</span>
          </div>
          <div ref="brandChartRef" v-loading="loading" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <div class="card">
          <div class="card-title">
            车龄与价格关系
            <span class="card-sub" v-if="isFiltered">已联动筛选</span>
          </div>
          <div ref="ageChartRef" v-loading="loading" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :sm="24" :md="12">
        <div class="card">
          <div class="card-title">
            价格分布
            <span class="card-sub" v-if="isFiltered">已联动筛选</span>
          </div>
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
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import { getDashboardSummary, getBrandPriceTop10, getStatAggregate, getCarBrands, getCarCities } from '@/api'

const summary = ref({})
const loading = ref(false)
const brandChartRef = ref(null)
const ageChartRef = ref(null)
const priceDistChartRef = ref(null)

const brands = ref([])
const cities = ref([])

// 筛选状态
const filters = reactive({ brand: '', city: '', price_range: '' })
const priceRanges = [
  { label: '价格不限', value: '' },
  { label: '0-5万', value: '0-5' },
  { label: '5-10万', value: '5-10' },
  { label: '10-15万', value: '10-15' },
  { label: '15-20万', value: '15-20' },
  { label: '20-30万', value: '20-30' },
  { label: '30-50万', value: '30-50' },
  { label: '50万以上', value: '50-' }
]
const isFiltered = computed(() => !!(filters.brand || filters.city || filters.price_range))

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

// 组装聚合接口参数
const buildAggParams = () => {
  const p = {}
  if (filters.brand) p.brand = filters.brand
  if (filters.city) p.city = filters.city
  if (filters.price_range) {
    const [lo, hi] = filters.price_range.split('-')
    if (lo) p.min_price = lo
    if (hi) p.max_price = hi
  }
  return p
}

const initCharts = () => {
  if (brandChartRef.value) brandChart = echarts.init(brandChartRef.value)
  if (ageChartRef.value) ageChart = echarts.init(ageChartRef.value)
  if (priceDistChartRef.value) priceDistChart = echarts.init(priceDistChartRef.value)
}

const loadBrands = async () => {
  try {
    const res = await getCarBrands()
    brands.value = res.brands || []
  } catch (e) {
    brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉']
  }
}

const loadCities = async () => {
  try {
    const res = await getCarCities()
    cities.value = res.cities || []
  } catch (e) {
    cities.value = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆']
  }
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
      grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
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
      dataZoom: [
        { type: 'slider', height: 14, bottom: 4, start: 0, end: 100, borderColor: '#E5E7EB' },
        { type: 'inside' }
      ],
      series: (res.series || []).map((s, i) => ({
        ...s,
        barMaxWidth: 24,
        itemStyle: {
          borderRadius: i === 0 ? [4, 4, 0, 0] : [0, 0, 4, 4],
          // 筛选品牌时高亮该品牌柱
          color: i === 0 ? (params) => {
            if (filters.brand && params.name === filters.brand) return '#F59E0B'
            return '#2D6BFF'
          } : '#B9D1FF'
        }
      }))
    })
  } catch (e) {
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

// 统一加载联动图表（车龄 + 价格分布 + 统计卡片）
const loadCharts = async () => {
  loading.value = true
  try {
    const res = await getStatAggregate(buildAggParams())
    if (res.code !== 200) return
    const d = res.data

    // 统计卡片联动（总量/均价跟随筛选）
    if (d.total_cars !== undefined) summary.value.total_cars = d.total_cars
    if (d.avg_price !== undefined) summary.value.avg_price = d.avg_price

    // 车龄-价格图
    if (ageChart) {
      const ac = d.age_chart || { xAxis: [], series: [] }
      ageChart.setOption({
        color: CHART_COLORS,
        tooltip: { trigger: 'axis' },
        legend: { data: ['平均售价', '车辆数量'], top: 0, textStyle: { color: '#4B5563' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          data: ac.xAxis || [],
          axisLabel: { color: '#6B7280', interval: 0 },
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
        series: (ac.series || []).map((s, i) => ({
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
    }

    // 价格分布图
    if (priceDistChart) {
      const pd = d.price_dist || { pie_data: [] }
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
          data: pd.pie_data || []
        }]
      })
    }
  } catch (e) {
    console.error('加载联动图表失败', e)
    // 兜底模拟数据
    ageChart?.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['0年','1年','2年','3年','4年','5年','6年','7年','8年','10年','12年','15年'] },
      yAxis: { type: 'value', name: '售价(万)' },
      series: [{ type: 'line', smooth: true, data: [22, 19, 16, 14, 12, 10, 8.5, 7.5, 6.5, 5, 4, 3], itemStyle: { color: '#2D6BFF' }, lineStyle: { width: 3 } }]
    })
    priceDistChart?.setOption({
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

const applyFilters = () => {
  loadCharts()
  loadBrandChart()  // 刷新 Top10（高亮选中品牌）
}

const resetFilters = () => {
  filters.brand = ''
  filters.city = ''
  filters.price_range = ''
  applyFilters()
}

const handleResize = () => {
  brandChart?.resize()
  ageChart?.resize()
  priceDistChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  await Promise.all([loadDashboard(), loadBrandChart(), loadCharts()])
  loadBrands()
  loadCities()
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

.filter-bar {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 12px 16px 0;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.filter-form { display: flex; flex-wrap: wrap; }

.stat-row { margin-bottom: 20px; }
.stat-row .el-col { margin-bottom: 12px; }
.chart-row { margin-bottom: 20px; }
.chart-row .el-col { margin-bottom: 12px; }

.card-sub {
  font-size: 12px;
  color: #9CA3AF;
  font-weight: 400;
  margin-left: 8px;
}

.stat-unit {
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 4px;
}
</style>
