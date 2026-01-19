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
      <div class="footer-gif-container">
        <div class="footer-gif" title="あまみはるかです！"></div>
        <div class="footer-tooltip">
          <span class="tooltip-text">✧はるかっかー✧</span>
        </div>
      </div>
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

/* Footer GIF和Tooltip样式 */
.footer-gif-container {
  position: relative;
  display: inline-block;
  margin-bottom: 16px;
}

.footer-gif {
  width: 100px;
  height: 100px;
  background-image: var(--footer-gif);
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  opacity: 0.8;
}

.footer-gif:hover {
  opacity: 1;
  transform: scale(1.1) rotate(5deg);
  filter: brightness(1.2) saturate(1.3);
}

.footer-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  z-index: 1000;
  margin-bottom: 8px;
}

.footer-gif-container:hover .footer-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-5px);
}

.tooltip-text {
  display: inline-block;
  padding: 8px 12px;
  background: linear-gradient(135deg, #ff6b9d, #ffa8cc);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.4);
  position: relative;
  animation: bounce 2s infinite;
}

.tooltip-text::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid #ff6b9d;
}

/* 可爱的弹跳动画 */
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0) translateX(-50%);
  }
  40% {
    transform: translateY(-3px) translateX(-50%);
  }
  60% {
    transform: translateY(-2px) translateX(-50%);
  }
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

  /* 移动端gif和tooltip优化 */
  .footer-gif {
    width: 48px;
    height: 48px;
  }

  .tooltip-text {
    font-size: 11px;
    padding: 6px 10px;
    max-width: 200px;
    white-space: normal;
    text-align: center;
    line-height: 1.3;
  }

  /* 移动端触摸优化 */
  .footer-gif-container:active .footer-tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(-5px);
  }
}
</style>
