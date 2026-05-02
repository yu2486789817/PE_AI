<template>
  <view class="list-card" @click="$emit('click')">
    <slot />
  </view>
</template>

<script setup>
defineEmits(['click'])
</script>

<style scoped>
.list-card {
  background: var(--color-surface-card);
  border: 2rpx solid var(--color-line-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 22rpx;
}
</style>
