<template>
  <view class="form-block">
    <text class="form-block__label">{{ label }}</text>
    <slot />
  </view>
</template>

<script setup>
defineProps({ label: { type: String, required: true } })
</script>

<style scoped>
.form-block {
  margin-bottom: 20rpx;
}
.form-block__label {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
  color: var(--color-ink-600);
  margin-bottom: 10rpx;
}
</style>
