<template>
  <view class="info-card">
    <view v-if="title" class="info-card__header">
      <text class="info-card__title">{{ title }}</text>
      <slot name="extra" />
    </view>
    <view class="info-card__body">
      <slot />
    </view>
  </view>
</template>

<script setup>
defineProps({ title: { type: String, default: '' } })
</script>

<style scoped>
.info-card {
  background: var(--color-surface-card);
  border: 2rpx solid var(--color-line-200);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}
.info-card__header {
  padding: 20rpx 24rpx;
  border-bottom: 2rpx solid var(--color-line-100);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.info-card__title {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--color-ink-900);
}
.info-card__body {
  padding: 24rpx;
}
</style>
