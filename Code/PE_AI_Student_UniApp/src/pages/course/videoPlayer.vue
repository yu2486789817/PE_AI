<template>
	<PageLayout>
		<view class="container">
			<view class="title-row">
				<text class="title">{{ title || '视频播放' }}</text>
			</view>
			<video
				v-if="url"
				:src="url"
				class="player"
				controls
				autoplay
				object-fit="contain"
				@error="onVideoError"
			/>
			<view v-else class="empty">
				<text class="empty-text">视频地址无效</text>
			</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import PageLayout from '@/components/PageLayout.vue';

const url = ref('');
const title = ref('');

onMounted(() => {
	const pages = getCurrentPages();
	const page = pages[pages.length - 1];
	url.value = decodeURIComponent(page?.options?.url || '');
	title.value = decodeURIComponent(page?.options?.title || '');
});

const onVideoError = () => {
	uni.showToast({ title: '视频加载失败', icon: 'none' });
};
</script>

<style scoped>
.container {
	padding: 24rpx;
	min-height: 100vh;
}

.title-row {
	margin-bottom: 16rpx;
}

.title {
	font-size: 30rpx;
	font-weight: 700;
	color: #1f2f53;
}

.player {
	width: 100%;
	height: 420rpx;
	border-radius: 18rpx;
	background: #000;
}

.empty {
	padding: 80rpx 0;
	text-align: center;
}

.empty-text {
	font-size: 24rpx;
	color: #6d7b9b;
}
</style>
