<template>
  <div>
    <h2>Banner显示测试</h2>
    
    <!-- 调试信息 -->
    <div style="background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 4px;">
      <h3>调试信息</h3>
      <p>banners数组长度: {{ banners.length }}</p>
      <p>API数据: {{ JSON.stringify(banners, null, 2) }}</p>
    </div>
    
    <!-- Banner轮播 -->
    <el-carousel :interval="5000" height="300px" class="banner-carousel" v-if="banners.length > 0">
      <el-carousel-item v-for="(item, index) in banners" :key="index">
        <div 
          class="banner-item" 
          :style="{ 
            backgroundColor: item.color,
            backgroundImage: item.image_url ? `url(${item.image_url})` : 'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat'
          }"
        >
          <div class="banner-content-overlay">
            <div class="banner-content">
              <h2>{{ item.title }}</h2>
              <p>{{ item.content }}</p>
              <p><small>图片: {{ item.image_url || '无' }}</small></p>
              <el-button v-if="item.link" type="primary" size="large" @click="handleClick(item.link)">
                {{ item.button_text || '了解更多' }}
              </el-button>
            </div>
          </div>
        </div>
      </el-carousel-item>
    </el-carousel>
    
    <!-- 无数据时显示 -->
    <div v-else class="no-banner">
      <p>没有Banner数据</p>
      <el-button @click="testHardcodedData">测试硬编码数据</el-button>
      <el-button @click="fetchBanners">重新获取API数据</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getBanners } from '../api'

const router = useRouter()
const banners = ref([])

const handleClick = (link) => {
  if (link) {
    if (link.startsWith('/')) {
      router.push(link)
    } else {
      window.open(link, '_blank')
    }
  }
}

const testHardcodedData = () => {
  console.log('使用硬编码测试数据')
  banners.value = [
    {
      id: 999,
      title: '测试Banner',
      content: '这是硬编码的测试数据',
      image_url: '/media/banners/banner_2_20260119_165754.png',
      link: 'https://example.com',
      button_text: '测试按钮',
      color: '#409EFF',
      priority: 1,
      is_active: true
    }
  ]
}

const fetchBanners = async () => {
  try {
    console.log('正在获取Banner数据...')
    const data = await getBanners()
    console.log('API返回原始数据:', data)
    console.log('数据类型:', typeof data)
    console.log('是否是数组:', Array.isArray(data))
    
    if (data) {
      if (Array.isArray(data)) {
        banners.value = data
        console.log('直接使用数组数据:', banners.value)
      } else if (data.data && Array.isArray(data.data)) {
        banners.value = data.data
        console.log('使用data字段中的数组:', banners.value)
      } else if (data.results && Array.isArray(data.results)) {
        banners.value = data.results
        console.log('使用results字段中的数组:', banners.value)
      } else {
        console.warn('未知的数据格式:', data)
        banners.value = []
      }
    } else {
      console.warn('API返回空数据')
      banners.value = []
    }
  } catch (error) {
    console.error('获取 Banner 失败:', error)
    banners.value = []
  }
}

onMounted(() => {
  fetchBanners()
})
</script>

<style scoped>
.banner-carousel {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
}

.banner-item {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.banner-content-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.banner-content {
  text-align: center;
  padding: 20px;
  position: relative;
  z-index: 2;
}

.banner-content h2 {
  font-size: 36px;
  margin: 0 0 15px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.banner-content p {
  font-size: 18px;
  margin: 0 0 25px 0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

.no-banner {
  text-align: center;
  padding: 50px;
  background: #f5f5f5;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .banner-content h2 {
    font-size: 24px;
  }
  
  .banner-content p {
    font-size: 14px;
  }
}
</style>