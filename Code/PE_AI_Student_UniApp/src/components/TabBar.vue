<template>
	<view class="tabbar-container">
		<view
			v-for="(item, index) in tabList"
			:key="index"
			class="tab-item"
			:class="{ active: currentPath === item.pagePath }"
			@click="switchTab(item.pagePath)"
		>
			<view class="icon-wrapper">
				<image class="tab-icon" :src="currentPath === item.pagePath ? item.activeIcon : item.icon" mode="aspectFit" />
			</view>
			<text class="tab-text">{{ item.text }}</text>
			<view class="active-indicator" v-if="currentPath === item.pagePath"></view>
		</view>
	</view>
</template>

<script setup>
import { onMounted } from 'vue'

const props = defineProps({
	currentPath: {
		type: String,
		default: '/pages/index/index'
	}
})

const tabList = [
	{ id: 'home', text: '首页', pagePath: '/pages/index/index', icon: '/static/tabbar/home.png', activeIcon: '/static/tabbar/home-active.png' },
	{ id: 'assignment', text: '作业', pagePath: '/pages/assignments/list', icon: '/static/tabbar/assignment.png', activeIcon: '/static/tabbar/assignment-active.png' },
	{ id: 'chat', text: 'AI 助手', pagePath: '/pages/assistant/chat', icon: '/static/tabbar/chat.png', activeIcon: '/static/tabbar/chat-active.png' },
	{ id: 'profile', text: '我的', pagePath: '/pages/profile/index', icon: '/static/tabbar/profile.png', activeIcon: '/static/tabbar/profile-active.png' }
]

onMounted(() => {
	uni.hideTabBar({
		animation: false,
		fail: () => {}
	})
})

const switchTab = (path) => {
	if (props.currentPath === path) return
	uni.switchTab({
		url: path,
		fail: () => {
			uni.navigateTo({ url: path })
		}
	})
}
</script>

<style scoped>
.tabbar-container {
	position: fixed;
	bottom: calc(22rpx + env(safe-area-inset-bottom));
	left: 30rpx;
	right: 30rpx;
	height: var(--tabbar-height);
	border-radius: 40rpx;
	display: flex;
	align-items: center;
	justify-content: space-around;
	padding: 0 20rpx;
	z-index: 1000;
	box-shadow: var(--shadow-card);
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid var(--color-line-200);
}

.tab-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	flex: 1;
	height: 100%;
	position: relative;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.icon-wrapper {
	width: 44rpx;
	height: 44rpx;
	margin-bottom: 6rpx;
	color: var(--color-ink-500);
	transition: all 0.3s ease;
}

.tab-icon {
	width: 100%;
	height: 100%;
	display: block;
}

.tab-text {
	font-size: 20rpx;
	color: var(--color-ink-500);
	font-weight: 500;
	transition: all 0.3s ease;
}

.tab-item.active .icon-wrapper {
	color: var(--color-primary-600);
	transform: translateY(-4rpx);
}

.tab-item.active .tab-text {
	color: var(--color-primary-600);
	font-weight: 700;
}

.active-indicator {
	position: absolute;
	bottom: 12rpx;
	width: 8rpx;
	height: 8rpx;
	border-radius: 50%;
	background: var(--color-primary-600);
	box-shadow: 0 0 10rpx rgba(35, 109, 242, 0.5);
}
</style>
