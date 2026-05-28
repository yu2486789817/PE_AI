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
  background: #ffffff;
  border: 2rpx solid #d8e0ee;
  border-radius: 28rpx;
  box-shadow: 0 10rpx 24rpx rgba(23, 56, 122, 0.1);
  overflow: hidden;
}
.info-card__header {
  padding: 20rpx 24rpx;
  border-bottom: 2rpx solid #e8edf7;
  background: linear-gradient(90deg, #f6f9ff 0%, #ffffff 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.info-card__title {
  font-size: 30rpx;
  font-weight: 700;
  color: #172033;
}
.info-card__body {
  padding: 24rpx;
}
</style>
