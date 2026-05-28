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
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 2rpx solid #d8e0ee;
  border-radius: 22rpx;
  box-shadow: 0 10rpx 24rpx rgba(23, 56, 122, 0.1);
  padding: 22rpx;
}

.list-card:nth-child(2n) {
  background: linear-gradient(180deg, #ffffff 0%, #f4fbf8 100%);
}
</style>
