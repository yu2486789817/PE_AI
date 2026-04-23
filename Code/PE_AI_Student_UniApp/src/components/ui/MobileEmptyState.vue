<template>
  <view class="mobile-empty">
    <text class="mobile-empty__title">{{ title }}</text>
    <text class="mobile-empty__desc">{{ description }}</text>
    <view v-if="$slots.actions" class="mobile-empty__actions"><slot name="actions" /></view>
  </view>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.mobile-empty {
  text-align: center;
  padding: 80rpx 24rpx;
  border: 2rpx dashed var(--color-line-200);
  border-radius: var(--radius-lg);
  background: var(--color-surface-100);
}
.mobile-empty__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: var(--color-ink-800);
}
.mobile-empty__desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: var(--color-ink-500);
}
.mobile-empty__actions {
  margin-top: 18rpx;
}
</style>
