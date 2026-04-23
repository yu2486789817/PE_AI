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
				<view v-if="item.id === 'home'" class="svg-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
						<polyline points="9 22 9 12 15 12 15 22"></polyline>
					</svg>
				</view>
				<view v-else-if="item.id === 'assignment'" class="svg-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
						<polyline points="14 2 14 8 20 8"></polyline>
						<line x1="16" y1="13" x2="8" y2="13"></line>
						<line x1="16" y1="17" x2="8" y2="17"></line>
					</svg>
				</view>
				<view v-else-if="item.id === 'chat'" class="svg-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
						<circle cx="9" cy="9" r="0.5" fill="currentColor"></circle>
						<circle cx="15" cy="9" r="0.5" fill="currentColor"></circle>
					</svg>
				</view>
				<view v-else-if="item.id === 'profile'" class="svg-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
						<circle cx="12" cy="7" r="4"></circle>
					</svg>
				</view>
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
	{ id: 'home', text: '首页', pagePath: '/pages/index/index' },
	{ id: 'assignment', text: '作业', pagePath: '/pages/assignments/list' },
	{ id: 'chat', text: 'AI 助手', pagePath: '/pages/assistant/chat' },
	{ id: 'profile', text: '我的', pagePath: '/pages/profile/index' }
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
	bottom: 30rpx;
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
	margin-bottom: var(--safe-area-bottom);
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
	width: 48rpx;
	height: 48rpx;
	margin-bottom: 6rpx;
	color: var(--color-ink-500);
	transition: all 0.3s ease;
}

.svg-icon {
	width: 100%;
	height: 100%;
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
