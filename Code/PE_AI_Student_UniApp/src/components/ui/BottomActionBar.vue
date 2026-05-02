<template>
  <view class="bottom-action-bar"><slot /></view>
</template>

<style scoped>
.bottom-action-bar {
  position: sticky;
  bottom: calc(var(--tabbar-height) + var(--safe-area-bottom) + 10rpx);
  z-index: 20;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid var(--color-line-200);
  border-radius: 999rpx;
  padding: 12rpx;
  box-shadow: var(--shadow-card);
}
</style>
