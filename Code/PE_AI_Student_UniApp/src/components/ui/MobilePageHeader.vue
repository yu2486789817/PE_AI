<template>
  <view class="mobile-header">
    <view>
      <text class="mobile-header__title">{{ title }}</text>
      <text v-if="subtitle" class="mobile-header__subtitle">{{ subtitle }}</text>
    </view>
    <view v-if="$slots.actions" class="mobile-header__actions">
      <slot name="actions" />
    </view>
  </view>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>

<style scoped>
.mobile-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
}
.mobile-header__title {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: var(--color-ink-900);
}
.mobile-header__subtitle {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: var(--color-ink-500);
}
.mobile-header__actions {
  display: flex;
  gap: 12rpx;
}
</style>
