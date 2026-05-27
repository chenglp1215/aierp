<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="dashboard-footer">
    <div class="footer-left">
      <span class="footer-copyright">© {{ currentYear }} ERP Platform. All rights reserved.</span>
    </div>
    <div class="footer-right">
      <span class="footer-version">Version 1.0.0</span>
      <span class="footer-divider">|</span>
      <a href="#" class="footer-link">隐私政策</a>
      <span class="footer-divider">|</span>
      <a href="#" class="footer-link">使用条款</a>
    </div>
  </footer>
</template>

<style scoped>
.dashboard-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 48px;
  background-color: var(--color-canvas);
  border-top: 1px solid var(--color-hairline);
}

.footer-left {
  display: flex;
  align-items: center;
}

.footer-copyright {
  font-size: 12px;
  color: var(--color-muted);
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-version {
  font-size: 12px;
  color: var(--color-muted);
}

.footer-divider {
  font-size: 12px;
  color: var(--color-muted);
}

.footer-link {
  font-size: 12px;
  color: var(--color-muted);
  transition: color var(--transition-fast);
}

.footer-link:hover {
  color: var(--color-interactive);
}

@media (max-width: 768px) {
  .dashboard-footer {
    flex-direction: column;
    height: auto;
    padding: 12px 24px;
    gap: 8px;
  }
}
</style>