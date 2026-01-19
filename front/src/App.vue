<template>
  <div id="app">
    <Navbar />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <footer class="footer">
      <div class="footer-gif"></div>
      <p>&copy; 2026 XMMCG. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 24px;
  background: transparent;
  color: var(--text-primary);
}

.footer {
  background: var(--surface-strong);
  backdrop-filter: blur(var(--glass-blur));
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
  text-align: center;
  padding: 20px;
  margin-top: auto;
}

.footer p {
  margin: 0;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .main-content {
    padding: 12px;
  }

  .footer {
    padding: 16px 12px;
    font-size: 14px;
  }
}
</style>
