<template>
	<view class="layout-container" :class="{ 'lock-scroll': lockScroll }">
		<!-- 顶部状态栏占位 -->
		<view v-if="showStatusBar" class="status-bar" :style="{ height: statusBarHeight + 'px' }"></view>
		
		<!-- 页面核心内容 -->
		<view class="content-wrapper" :class="{ 'no-tabbar': !showTabBar, 'lock-scroll': lockScroll }">
			<slot></slot>
		</view>
		
		<!-- 全局自定义 TabBar -->
		<TabBar v-if="showTabBar" :currentPath="currentPath" />
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import TabBar from './TabBar.vue';

defineProps({
	showTabBar: {
		type: Boolean,
		default: true
	},
	lockScroll: {
		type: Boolean,
		default: false
	},
	showStatusBar: {
		type: Boolean,
		default: true
	}
});

const statusBarHeight = ref(0);
const currentPath = ref('');

onMounted(() => {
	// 获取系统状态栏高度
	const windowInfo = uni.getWindowInfo ? uni.getWindowInfo() : {};
	statusBarHeight.value = windowInfo.statusBarHeight || 0;
	
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

.layout-container.lock-scroll {
	height: 100vh;
	overflow: hidden;
}

.content-wrapper {
	flex: 1;
	padding-bottom: 240rpx;
	display: flex;
	flex-direction: column;
}

.content-wrapper.no-tabbar {
	padding-bottom: 0;
}

.content-wrapper.lock-scroll {
	min-height: 0;
	overflow: hidden;
}

.status-bar {
	width: 100%;
}
</style>
