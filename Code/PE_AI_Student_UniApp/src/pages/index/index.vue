<template>
	<PageLayout>
		<view class="container">
		<view class="banner">
			<text class="banner-title">智慧运动课堂</text>
			<text class="banner-sub">记录每一次进步，让训练反馈更清晰、更科学。</text>
		</view>

		<view class="action-grid">
			<view class="action-item" @click="goTo('/pages/assignments/list')">
				<view class="action-icon text-blue">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
						<polyline points="14 2 14 8 20 8"></polyline>
						<line x1="16" y1="13" x2="8" y2="13"></line>
						<line x1="16" y1="17" x2="8" y2="17"></line>
						<polyline points="10 9 9 9 8 9"></polyline>
					</svg>
				</view>
				<text class="action-text">我的作业</text>
			</view>
			<view class="action-item" @click="goTo('/pages/assistant/chat')">
				<view class="action-icon text-blue">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">
						<rect x="3" y="11" width="18" height="10" rx="2"></rect>
						<circle cx="12" cy="5" r="2"></circle>
						<path d="M12 7v4"></path>
						<line x1="8" y1="16" x2="8" y2="16"></line>
						<line x1="16" y1="16" x2="16" y2="16"></line>
					</svg>
				</view>
				<text class="action-text">AI 助手</text>
			</view>
		</view>

		<view class="section-header">
			<text class="section-title">我的课程</text>
			<text class="add-btn" @click="showJoinDialog = true">+ 加入课程</text>
		</view>

		<view class="loading" v-if="loadingCourses"><text class="loading-text">正在加载课程...</text></view>

		<view class="empty" v-else-if="courses.length === 0">
			<text class="empty-text">暂无课程，点击右上角“加入课程”开始学习</text>
		</view>

		<view class="course-card" v-for="c in courses" :key="c.id" @click="goToCourse(c)">
			<view class="course-top">
				<text class="course-name">{{ c.name }}</text>
				<text :class="['course-status', c.statusClass]">{{ c.statusText }}</text>
			</view>
			<text class="course-desc">{{ c.description }}</text>
			<view class="course-bottom">
				<text class="course-meta">作业: {{ c.completedAssignments }}/{{ c.totalAssignments }}</text>
				<text class="course-meta">完成率: {{ c.completionRate }}%</text>
			</view>
		</view>

		<view class="mask" v-if="showJoinDialog" @click="showJoinDialog = false">
			<view class="dialog" @click.stop>
				<text class="dialog-title">加入课程</text>
				<input class="dialog-input" v-model="courseCode" placeholder="请输入 6 位课程码" maxlength="6" />
				<view class="dialog-btns">
					<button class="dialog-cancel" @click="showJoinDialog = false">取消</button>
					<button class="dialog-confirm" @click="handleJoin">加入</button>
				</view>
			</view>
		</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getStudentCourses, joinCourse } from '@/services/course';
import PageLayout from '@/components/PageLayout.vue';

const courses = ref([]);
const loadingCourses = ref(false);
const showJoinDialog = ref(false);
const courseCode = ref('');

onMounted(() => {
	fetchCourses();
});

const fetchCourses = async () => {
	loadingCourses.value = true;
	const user = uni.getStorageSync('user');
	if (!user?.id) {
		loadingCourses.value = false;
		return;
	}

	const res = await getStudentCourses(user.id);
	if (res.success && res.data) {
		courses.value = res.data.map(c => {
			const active = c.isActive === '1';
			return {
				...c,
				description: c.info || '',
				statusText: active ? '进行中' : '已结束',
				statusClass: active ? 'active' : 'ended',
				totalAssignments: 0,
				completedAssignments: 0,
				completionRate: 0
			};
		});
	} else {
		courses.value = [];
	}
	loadingCourses.value = false;
};

const handleJoin = async () => {
	if (!courseCode.value || courseCode.value.length !== 6) {
		uni.showToast({ title: '请输入 6 位课程码', icon: 'none' });
		return;
	}
	const user = uni.getStorageSync('user');
	const res = await joinCourse(user?.id, courseCode.value);
	if (res.success) {
		uni.showToast({ title: '加入成功' });
		showJoinDialog.value = false;
		courseCode.value = '';
		fetchCourses();
	} else {
		uni.showToast({ title: res.message || '加入失败', icon: 'none' });
	}
};

const goTo = (url) => uni.switchTab({ url });
const goToCourse = (c) => uni.navigateTo({ url: `/pages/course/detail?id=${c.id}` });
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.banner {
	position: relative;
	overflow: hidden;
	border-radius: 30rpx;
	padding: 52rpx 36rpx;
	margin-bottom: 26rpx;
	background: linear-gradient(125deg, #1554e6 0%, #2787ff 48%, #20c3ff 100%);
	box-shadow: 0 20rpx 40rpx rgba(17, 66, 170, 0.28);
}

.banner::after {
	content: '';
	position: absolute;
	width: 260rpx;
	height: 260rpx;
	border-radius: 50%;
	background: rgba(255, 255, 255, 0.16);
	right: -110rpx;
	top: -110rpx;
}

.banner-title {
	display: block;
	position: relative;
	font-size: 42rpx;
	font-weight: 700;
	color: #fff;
}

.banner-sub {
	display: block;
	position: relative;
	margin-top: 12rpx;
	font-size: 24rpx;
	line-height: 1.6;
	color: rgba(255, 255, 255, 0.9);
}

.action-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 18rpx;
	margin-bottom: 28rpx;
}

.action-item {
	height: 148rpx;
	background: rgba(255, 255, 255, 0.9);
	border: 2rpx solid rgba(255, 255, 255, 0.85);
	border-radius: 24rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	box-shadow: 0 10rpx 24rpx rgba(23, 53, 120, 0.1);
}

.action-icon {
	width: 52rpx;
	height: 52rpx;
	margin-bottom: 12rpx;
}

.action-text {
	font-size: 25rpx;
	font-weight: 600;
	color: #1f3159;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16rpx;
}

.section-title {
	font-size: 31rpx;
	font-weight: 700;
	color: #1e2b49;
}

.add-btn {
	padding: 12rpx 22rpx;
	font-size: 24rpx;
	font-weight: 600;
	color: #1c5fed;
	background: rgba(29, 99, 255, 0.1);
	border-radius: 999rpx;
}

.loading,
.empty {
	padding: 72rpx 20rpx;
	text-align: center;
}

.loading-text,
.empty-text {
	font-size: 24rpx;
	color: #6a7898;
	line-height: 1.7;
}

.course-card {
	background: rgba(255, 255, 255, 0.9);
	border: 2rpx solid rgba(255, 255, 255, 0.86);
	border-radius: 24rpx;
	padding: 24rpx;
	margin-bottom: 18rpx;
	box-shadow: 0 10rpx 24rpx rgba(25, 54, 118, 0.1);
}

.course-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10rpx;
}

.course-name {
	font-size: 30rpx;
	font-weight: 700;
	color: #1c2b4f;
}

.course-status {
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

.course-desc {
	display: block;
	font-size: 24rpx;
	line-height: 1.6;
	color: #5d6c8e;
	margin-bottom: 14rpx;
}

.course-bottom {
	display: flex;
	gap: 20rpx;
}

.course-meta {
	font-size: 22rpx;
	color: #6a7898;
}

.mask {
	position: fixed;
	inset: 0;
	background: rgba(10, 20, 44, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 999;
}

.dialog {
	width: 84%;
	background: #fff;
	border-radius: 28rpx;
	padding: 36rpx;
	box-shadow: 0 20rpx 40rpx rgba(19, 44, 103, 0.2);
}

.dialog-title {
	display: block;
	text-align: center;
	font-size: 32rpx;
	font-weight: 700;
	color: #1d2d50;
	margin-bottom: 24rpx;
}

.dialog-input {
	height: 88rpx;
	border-radius: 16rpx;
	padding: 0 20rpx;
	text-align: center;
	font-size: 30rpx;
	letter-spacing: 8rpx;
	background: #f2f6ff;
	border: 2rpx solid #dce7ff;
}

.dialog-btns {
	display: flex;
	gap: 16rpx;
	margin-top: 24rpx;
}

.dialog-cancel,
.dialog-confirm {
	flex: 1;
	height: 80rpx;
	line-height: 80rpx;
	font-size: 27rpx;
	font-weight: 600;
	border-radius: 999rpx;
}

.dialog-cancel {
	background: #f0f3fb;
	color: #4f5d7f;
}

.dialog-confirm {
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	color: #fff;
}
</style>
