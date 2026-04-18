<template>
	<PageLayout>
		<view class="container">
		<view class="loading" v-if="loading"><text class="loading-text">正在加载作业...</text></view>

		<view class="empty" v-else-if="assignments.length === 0">
			<view class="empty-icon text-blue">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">
					<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
					<polyline points="14 2 14 8 20 8"></polyline>
					<line x1="16" y1="13" x2="8" y2="13"></line>
					<line x1="16" y1="17" x2="8" y2="17"></line>
					<polyline points="10 9 9 9 8 9"></polyline>
				</svg>
			</view>
			<text class="empty-text">当前没有可查看的作业</text>
		</view>

		<view v-else>
			<view class="assignment-card" v-for="item in assignments" :key="item.id" @click="goToDetail(item)">
				<view class="card-top">
					<text class="card-title">{{ item.title }}</text>
					<text :class="['status-tag', item.statusClass]">{{ item.statusText }}</text>
				</view>
				<text class="card-course">{{ item.courseName }}</text>
				<text class="card-desc">{{ item.description }}</text>
				<text class="card-deadline">截止时间: {{ formatDate(item.deadline) }}</text>
			</view>
		</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getStudentAssignments } from '@/services/studentAssignments';
import PageLayout from '@/components/PageLayout.vue';

const assignments = ref([]);
const loading = ref(true);

onMounted(() => {
	loadAssignments();
});

const loadAssignments = async () => {
	loading.value = true;
	const user = uni.getStorageSync('user');
	if (!user?.id) {
		loading.value = false;
		return;
	}

	const res = await getStudentAssignments(user.id);
	if (res.success && res.data) {
		assignments.value = res.data.map(hw => {
			const isActive = hw.deadline && new Date(hw.deadline) > new Date();
			return {
				...hw,
				courseName: '',
				statusText: isActive ? '进行中' : '已截止',
				statusClass: isActive ? 'active' : 'ended'
			};
		});
	}
	loading.value = false;
};

const formatDate = (s) => {
	if (!s) return '待定';
	const d = new Date(s);
	if (Number.isNaN(d.getTime())) return s;
	return `${d.getMonth() + 1}月${d.getDate()}日`;
};

const goToDetail = (item) => {
	uni.navigateTo({ url: `/pages/assignments/detail?id=${item.id}&courseId=${item.courseId}` });
};
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.loading,
.empty {
	padding: 110rpx 20rpx;
	text-align: center;
}

.loading-text,
.empty-text {
	font-size: 24rpx;
	color: #6d7b9b;
}

.empty-icon {
	width: 80rpx;
	height: 80rpx;
	margin: 0 auto 20rpx;
	color: var(--ink-500);
}

.assignment-card {
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 24rpx;
	padding: 24rpx;
	margin-bottom: 18rpx;
	box-shadow: 0 12rpx 26rpx rgba(25, 54, 118, 0.1);
}

.card-top {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 18rpx;
	margin-bottom: 8rpx;
}

.card-title {
	font-size: 29rpx;
	font-weight: 700;
	line-height: 1.4;
	color: #1f2e52;
}

.status-tag {
	padding: 6rpx 16rpx;
	border-radius: 999rpx;
	font-size: 21rpx;
	font-weight: 600;
}

.active {
	background: rgba(18, 185, 129, 0.14);
	color: #0d8b5f;
}

.ended {
	background: rgba(111, 122, 150, 0.16);
	color: #5b6683;
}

.card-course {
	display: inline-block;
	padding: 6rpx 12rpx;
	margin-bottom: 10rpx;
	font-size: 22rpx;
	color: #1f61ec;
	background: rgba(29, 99, 255, 0.1);
	border-radius: 999rpx;
}

.card-desc {
	display: block;
	font-size: 24rpx;
	line-height: 1.6;
	color: #607094;
	margin-bottom: 10rpx;
}

.card-deadline {
	font-size: 22rpx;
	font-weight: 600;
	color: #4f5f82;
}
</style>
