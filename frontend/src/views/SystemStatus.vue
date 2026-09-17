<template>
  <div>
    <!-- 集群拓扑 -->
    <div class="card" style="margin-bottom:20px">
      <div class="card-title">
        <span>集群拓扑</span>
        <el-tag type="danger" effect="light" size="small" round>3 节点分布式</el-tag>
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

    <!-- 组件版本 + 端口 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="12">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title">
            <span>组件版本清单</span>
            <el-tag type="primary" effect="light" size="small" round>/opt/module</el-tag>
          </div>
          <el-table :data="versions" size="small" stripe border>
            <el-table-column prop="name" label="组件" width="130">
              <template #default="{ row }">
                <span style="font-weight:600">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="version" label="版本" width="130" />
            <el-table-column prop="role" label="用途" min-width="180">
              <template #default="{ row }">
                <span style="color:#6B7280;font-size:12.5px">{{ row.role }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title">
            <span>服务端口</span>
            <el-tag type="success" effect="light" size="small" round>防火墙已放行</el-tag>
          </div>
          <el-table :data="ports" size="small" stripe border>
            <el-table-column prop="port" label="端口" width="100">
              <template #default="{ row }">
                <span style="font-weight:700;color:#2D6BFF">{{ row.port }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="service" label="服务" width="150" />
            <el-table-column prop="desc" label="说明" min-width="160">
              <template #default="{ row }">
                <span style="color:#6B7280;font-size:12.5px">{{ row.desc }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <!-- 技术栈 -->
    <div class="card">
      <div class="card-title">
        <span>技术栈</span>
        <el-tag type="warning" effect="light" size="small" round>全栈 + 大数据 + ML</el-tag>
      </div>
      <div class="stack-tags">
        <el-tag v-for="t in stack" :key="t.name" :type="t.type" effect="light" size="large" round class="stack-tag">
          {{ t.name }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Platform } from '@element-plus/icons-vue'

const nodes = [
  {
    host: 'hadoop101', ip: '192.168.249.101', role: 'Master',
    services: ['NameNode', 'JobHistoryServer', 'Hive Metastore', 'HiveServer2', 'MySQL', 'Redis', 'Django', 'Nginx', 'Celery', 'ZooKeeper', 'Kafka']
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

const versions = [
  { name: 'Hadoop', version: '3.1.3', role: 'HDFS 存储 + YARN 资源调度' },
  { name: 'ZooKeeper', version: '3.5.7', role: '分布式协调服务' },
  { name: 'Kafka', version: '2.4.1', role: '消息队列（日志采集）' },
  { name: 'Hive', version: '3.1.2', role: '数据仓库分层建模（ODS/DWD）' },
  { name: 'Spark', version: '3.0.0', role: '离线聚合分析 + MLlib 实验' },
  { name: 'Sqoop', version: '1.4.6', role: 'MySQL ↔ HDFS 数据导入导出' },
  { name: 'Flume', version: '1.9.0', role: '日志采集（可选链路）' },
  { name: 'MySQL', version: 'MariaDB 10.3', role: '业务库 / 统计结果存储' },
  { name: 'JDK', version: '1.8.0_212', role: 'Java 运行环境' },
  { name: 'Python', version: '3.9', role: 'Django / sklearn / Celery' }
]

const ports = [
  { port: 80, service: 'Nginx', desc: '前端页面（Vue 构建产物）' },
  { port: 8000, service: 'Gunicorn', desc: 'Django REST API' },
  { port: 3306, service: 'MySQL', desc: '业务数据库' },
  { port: 6379, service: 'Redis', desc: '缓存 + Celery Broker' },
  { port: 9083, service: 'Hive Metastore', desc: '元数据服务' },
  { port: 10000, service: 'HiveServer2', desc: 'Hive JDBC 查询' },
  { port: 9870, service: 'NameNode', desc: 'HDFS Web UI' },
  { port: 8088, service: 'ResourceManager', desc: 'YARN Web UI' },
  { port: 2181, service: 'ZooKeeper', desc: '集群协调' },
  { port: 9092, service: 'Kafka', desc: '消息队列' }
]

const stack = [
  { name: 'Vue3 + Vite', type: 'success' },
  { name: 'Element Plus', type: 'success' },
  { name: 'ECharts 5', type: 'success' },
  { name: 'Django + DRF', type: 'primary' },
  { name: 'MySQL / MariaDB', type: 'primary' },
  { name: 'Redis', type: 'primary' },
  { name: 'Celery 异步任务', type: 'primary' },
  { name: 'Nginx', type: 'primary' },
  { name: 'Hadoop HDFS', type: 'warning' },
  { name: 'YARN', type: 'warning' },
  { name: 'ZooKeeper', type: 'warning' },
  { name: 'Kafka', type: 'warning' },
  { name: 'Flume', type: 'warning' },
  { name: 'Sqoop', type: 'warning' },
  { name: 'Hive', type: 'warning' },
  { name: 'Spark SQL', type: 'warning' },
  { name: 'Scikit-learn', type: 'danger' },
  { name: 'SHAP 可解释性', type: 'danger' }
]
</script>

<style scoped>
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

.stack-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stack-tag {
  font-size: 13px;
}
</style>
