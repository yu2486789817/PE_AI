<template>
	<view class="layout-container">
		<!-- 顶部状态栏占位 -->
		<view class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>
		
		<!-- 页面核心内容 -->
		<view class="content-wrapper">
			<slot></slot>
		</view>
		
		<!-- 全局自定义 TabBar -->
		<TabBar :currentPath="currentPath" />
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import TabBar from './TabBar.vue';

const statusBarHeight = ref(0);
const currentPath = ref('');

onMounted(() => {
	// 获取系统状态栏高度
	const systemInfo = uni.getSystemInfoSync();
	statusBarHeight.value = systemInfo.statusBarHeight || 0;
	
	// 获取当前页面路径
	const pages = getCurrentPages();
	if (pages.length > 0) {
		const currentPage = pages[pages.length - 1];
		currentPath.value = '/' + currentPage.route;
	}
});
</script>

<style scoped>
.layout-container {
	min-height: 100vh;
	display: flex;
	flex-direction: column;
	background-attachment: fixed;
}

.content-wrapper {
	flex: 1;
	padding-bottom: var(--page-bottom-padding);
	display: flex;
	flex-direction: column;
}

.status-bar {
	width: 100%;
}
</style>
