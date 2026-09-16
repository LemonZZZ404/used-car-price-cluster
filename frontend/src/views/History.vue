<template>
  <div class="history-page">
    <div class="card">
      <div class="card-title">
        <span>预测历史记录</span>
        <el-tag type="primary" effect="light" round>共 {{ total }} 条</el-tag>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border size="default">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="brand" label="品牌" width="90">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain" size="small">{{ row.brand }}</el-tag>
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
        <el-table-column prop="fuel_type" label="燃油类型" width="95" />
        <el-table-column prop="displacement" label="排量" width="80" />
        <el-table-column prop="city" label="城市" width="80" />
        <el-table-column prop="original_price" label="新车价(万)" width="100" />
        <el-table-column prop="predicted_price" label="预测价格(万)" width="120" sortable>
          <template #default="{ row }">
            <span style="color:#EF4444;font-weight:600">{{ row.predicted_price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="model_type" label="模型" width="130">
          <template #default="{ row }">
            <el-tag :type="row.model_type === 'sklearn' ? 'success' : 'warning'" size="small" effect="light" round>
              {{ row.model_type === 'sklearn' ? 'Scikit-learn' : row.model_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="预测时间" min-width="160" />
      </el-table>

      <el-empty v-if="!loading && tableData.length === 0" description="暂无预测记录" />

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
import { ref, onMounted } from 'vue'
import { getPredictionHistory } from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const loadData = async () => {
  loading.value = true
  try {
    const res = await getPredictionHistory({ limit: pageSize.value })
    if (res.code === 200) {
      tableData.value = res.data || []
      total.value = res.total || 0
    }
  } catch (e) {
    console.error('加载预测历史失败', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>
