<template>
  <div class="phase-timeline-container">
    <h2>竞赛阶段日程</h2>
    
    <el-timeline>
      <el-timeline-item
        v-for="(phase, index) in phases"
        :key="phase.id"
        :timestamp="`${formatDate(phase.start_time)} - ${formatDate(phase.end_time)}`"
        :placement="index % 2 === 0 ? 'top' : 'bottom'"
        :type="getPhaseType(phase.status)"
      >
        <div class="phase-item">
          <div class="phase-header">
            <h4>{{ phase.name }}</h4>
            <el-tag :type="getPhaseTagType(phase.status)" size="small">
              {{ getPhaseStatusText(phase.status) }}
            </el-tag>
          </div>
          
          <div class="phase-content">
            <p>{{ phase.description }}</p>
            
            <!-- 进度条 -->
            <el-progress 
              :percentage="phase.progress_percent"
              :status="phase.status === 'active' ? 'success' : ''"
              :show-text="true"
            />
            
            <!-- 剩余时间 -->
            <div class="phase-time-info">
              <span v-if="phase.status === 'upcoming'">
                <strong>距离开始：</strong> {{ phase.time_remaining }}
              </span>
              <span v-else-if="phase.status === 'active'">
                <strong style="color: #67C23A;">进行中，剩余：</strong> {{ phase.time_remaining }}
              </span>
              <span v-else>
                <strong>已结束</strong>
              </span>
            </div>
            
            <!-- 页面访问权限提示 -->
            <div class="phase-access-info">
              <span class="access-title">功能开放：</span>
              <el-tag v-if="phase.page_access?.songs" type="success" size="small">歌曲竞标</el-tag>
              <el-tag v-if="phase.page_access?.charts" type="success" size="small">谱面制作</el-tag>
              <el-tag v-if="phase.page_access?.profile" type="success" size="small">个人中心</el-tag>
              
              <el-tag v-if="!phase.page_access?.songs" type="info" size="small" style="opacity: 0.5;">歌曲（锁定）</el-tag>
              <el-tag v-if="!phase.page_access?.charts" type="info" size="small" style="opacity: 0.5;">谱面（锁定）</el-tag>
            </div>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCompetitionPhases } from '../api/index.js'

const phases = ref([])

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const getPhaseType = (status) => {
  switch (status) {
    case 'active':
      return 'success'
    case 'ended':
      return 'primary'
    default:
      return 'info'
  }
}

const getPhaseTagType = (status) => {
  switch (status) {
    case 'active':
      return 'success'
    case 'upcoming':
      return 'warning'
    case 'ended':
      return 'info'
    default:
      return 'info'
  }
}

const getPhaseStatusText = (status) => {
  switch (status) {
    case 'active':
      return '进行中'
    case 'upcoming':
      return '即将开始'
    case 'ended':
      return '已结束'
    default:
      return '未知'
  }
}

const loadPhases = async () => {
  try {
    const data = await getCompetitionPhases()
    phases.value = data
  } catch (error) {
    console.error('加载竞赛阶段失败:', error)
  }
}

onMounted(() => {
  loadPhases()
  
  // 每 30 秒刷新一次（更新剩余时间和进度）
  setInterval(() => {
    loadPhases()
  }, 30000)
})
</script>

<style scoped>
.phase-timeline-container {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-top: 20px;
}

.phase-timeline-container h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 600;
}

.phase-item {
  padding: 15px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.phase-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.phase-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.phase-content {
  padding-top: 10px;
}

.phase-content p {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
  font-size: 14px;
}

.phase-time-info {
  margin: 12px 0;
  padding: 8px 12px;
  background: #f9f9f9;
  border-left: 3px solid #409EFF;
  border-radius: 4px;
  font-size: 14px;
  color: #555;
}

.phase-time-info span {
  display: block;
}

.phase-access-info {
  margin-top: 12px;
  padding: 10px 0;
}

.access-title {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-right: 8px;
}

.access-title + .el-tag {
  margin-right: 6px;
  margin-bottom: 6px;
}
</style>
