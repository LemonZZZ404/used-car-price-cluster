<template>
  <div class="car-list-page">
    <!-- 搜索筛选区 -->
    <div class="card filter-card">
      <el-form :inline="true" :model="filterForm" size="default">
        <el-form-item label="品牌">
          <el-select v-model="filterForm.brand" placeholder="全部品牌" clearable filterable style="width:160px">
            <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格区间">
          <el-input-number v-model="filterForm.min_price" :min="0" :max="500" placeholder="最低" style="width:110px" />
          <span style="margin:0 8px;color:#9CA3AF">-</span>
          <el-input-number v-model="filterForm.max_price" :min="0" :max="500" placeholder="最高" style="width:110px" />
        </el-form-item>
        <el-form-item label="车龄">
          <el-input-number v-model="filterForm.min_age" :min="0" :max="30" placeholder="最低" style="width:90px" />
          <span style="margin:0 8px;color:#9CA3AF">-</span>
          <el-input-number v-model="filterForm.max_age" :min="0" :max="30" placeholder="最高" style="width:90px" />
        </el-form-item>
        <el-form-item label="变速箱">
          <el-select v-model="filterForm.gearbox" placeholder="全部" clearable style="width:110px">
            <el-option label="自动" value="自动" />
            <el-option label="手动" value="手动" />
          </el-select>
        </el-form-item>
        <el-form-item label="燃油类型">
          <el-select v-model="filterForm.fuel_type" placeholder="全部" clearable style="width:110px">
            <el-option v-for="f in fuelTypes" :key="f" :label="f" :value="f" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 车辆列表 -->
    <div class="card" style="margin-top:20px">
      <div class="card-title">
        <span>车辆列表</span>
        <el-tag type="primary" effect="light" round>共 {{ formatNumber(total) }} 条</el-tag>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border size="default">
        <el-table-column prop="car_id" label="车辆编号" width="130" />
        <el-table-column prop="brand" label="品牌" width="90">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain" size="small">{{ row.brand }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="series" label="车系" width="100" />
        <el-table-column prop="model" label="车型" min-width="180" show-overflow-tooltip />
        <el-table-column prop="price" label="售价(万)" width="100" sortable>
          <template #default="{ row }">
            <span class="price-text">{{ row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="age" label="车龄" width="70">
          <template #default="{ row }">{{ row.age }}年</template>
        </el-table-column>
        <el-table-column prop="mileage" label="里程(万)" width="90" />
        <el-table-column prop="gearbox" label="变速箱" width="80">
          <template #default="{ row }">
            <el-tag :type="row.gearbox === '自动' ? 'success' : 'info'" effect="plain" size="small">{{ row.gearbox }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fuel_type" label="燃油类型" width="95">
          <template #default="{ row }">
            <el-tag :type="fuelTagType(row.fuel_type)" effect="plain" size="small">{{ row.fuel_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="city" label="城市" width="90" />
      </el-table>

      <el-empty v-if="!loading && tableData.length === 0" description="没有符合条件的数据" />

      <div class="pagination" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getCarList, getCarBrands } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const brands = ref([])
const fuelTypes = ['汽油', '柴油', '纯电动', '混合动力', '插电混动']

const filterForm = reactive({
  brand: '',
  min_price: null,
  max_price: null,
  min_age: null,
  max_age: null,
  gearbox: '',
  fuel_type: ''
})

const formatNumber = (n) => {
  if (n === undefined || n === null) return 0
  return Number(n).toLocaleString('zh-CN')
}

const fuelTagType = (fuel) => {
  if (fuel === '纯电动') return 'success'
  if (fuel === '汽油') return 'warning'
  if (fuel === '柴油') return 'info'
  return 'primary'
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      ...filterForm
    }
    // 清理空值
    Object.keys(params).forEach(k => {
      if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
    })
    const res = await getCarList(params)
    tableData.value = res.results || res.data || []
    total.value = res.count || 0
  } catch (e) {
    console.error('加载车辆列表失败', e)
  } finally {
    loading.value = false
  }
}

const loadBrands = async () => {
  try {
    const res = await getCarBrands()
    brands.value = res.brands || []
  } catch (e) {
    brands.value = ['大众', '丰田', '本田', '日产', '别克', '奥迪', '宝马', '奔驰', '比亚迪', '特斯拉']
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const handleReset = () => {
  Object.assign(filterForm, {
    brand: '', min_price: null, max_price: null,
    min_age: null, max_age: null, gearbox: '', fuel_type: ''
  })
  page.value = 1
  loadData()
}

onMounted(() => {
  loadBrands()
  loadData()
})
</script>

<style scoped>
.filter-card { margin-bottom: 0; }
.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }

.price-text {
  color: #EF4444;
  font-weight: 600;
}

:deep(.el-table .cell) {
  padding: 0 10px;
}
</style>
