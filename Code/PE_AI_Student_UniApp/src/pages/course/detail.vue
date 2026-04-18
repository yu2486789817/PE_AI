<template>
	<PageLayout>
		<view class="container">
		<view class="loading" v-if="loading"><text class="loading-text">正在加载课程...</text></view>

		<view class="course-card" v-if="course">
			<text class="course-name">{{ course.name }}</text>
			<text class="course-desc">{{ course.description }}</text>
			<view class="info-row"><text class="info-label">课程号:</text><text class="info-val">{{ course.subject }}</text></view>
			<view class="info-row"><text class="info-label">教师:</text><text class="info-val">{{ course.teacherName }}</text></view>
			<view class="info-row">
				<text class="info-label">状态:</text>
				<text :class="['status-tag', course.statusClass]">{{ course.statusText }}</text>
			</view>
		</view>

		<view class="section" v-if="course" @click="goToVideos">
			<text class="section-title">教学视频</text>
			<text class="section-arrow">></text>
		</view>

		<view class="section-header" v-if="course"><text class="section-title">课程作业</text></view>

		<view class="assignment-card" v-for="item in assignments" :key="item.id" @click="goToAssignment(item)">
			<view class="assignment-top">
				<text class="assignment-title">{{ item.title }}</text>
				<text :class="['status-tag', item.statusClass]">{{ item.statusText }}</text>
			</view>
			<text class="assignment-desc">{{ item.description }}</text>
			<text class="assignment-deadline">截止时间: {{ formatDate(item.deadline) }}</text>
		</view>

		<view class="empty" v-if="course && assignments.length === 0"><text class="empty-text">暂无作业</text></view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import request from '@/services/request';
import PageLayout from '@/components/PageLayout.vue';

const course = ref(null);
const assignments = ref([]);
const loading = ref(true);
const courseId = ref('');

onMounted(() => {
	const pages = getCurrentPages();
	const page = pages[pages.length - 1];
	courseId.value = page.options?.id || '';
	loadCourseDetails();
});

const loadCourseDetails = async () => {
	loading.value = true;
	const user = uni.getStorageSync('user');
	const token = uni.getStorageSync('token');
	try {
		const courseResp = await request.post('/Course/get_info_by_course_id', { first: courseId.value });
		if (courseResp.data?.success && courseResp.data.data) {
			const d = courseResp.data.data.split('\t\r');
			const teacherId = d[0] || '';
			let teacherName = '未知教师';
			try {
				const tResp = await request.post('/User/get_teacher_info', {
					first: user?.id,
					second: token,
					third: '0',
					fourth: teacherId
				});
				if (tResp.data?.success && tResp.data.data) {
					teacherName = tResp.data.data.split('\t\r')[0] || '未知教师';
				}
			} catch (e) {
				// ignore teacher info failure
			}

			const active = d[5] === '1';
			course.value = {
				id: courseId.value,
				name: d[1] || '未命名课程',
				description: d[2] || '',
				subject: d[3] || '',
				statusText: active ? '进行中' : '已结束',
				statusClass: active ? 'active' : 'ended',
				teacherName
			};
		}

		const hwResp = await request.post('/Homework/get_homework_id_by_course', {
			first: '0',
			second: user?.id,
			third: token,
			fourth: courseId.value
		});

		if (hwResp.data?.success && hwResp.data.data && hwResp.data.data !== 'NULL') {
			const ids = hwResp.data.data.split('\t\r').filter((i) => i.trim());
			const items = [];
			for (const hwId of ids) {
				try {
					const infoResp = await request.post('/Homework/get_info_by_homework_id', {
						first: courseId.value,
						second: hwId.trim()
					});
					if (infoResp.data?.success && infoResp.data.data) {
						const ad = infoResp.data.data.split('\t\r');
						const active = ad[2] && new Date(ad[2]) > new Date();
						items.push({
							id: hwId.trim(),
							title: ad[0] || `作业 ${hwId}`,
							description: ad[1] || '',
							deadline: ad[2] || '',
							statusText: active ? '进行中' : '已截止',
							statusClass: active ? 'active' : 'ended'
						});
					}
				} catch (e) {
					// ignore one homework failure
				}
			}
			assignments.value = items;
		} else {
			assignments.value = [];
		}
	} catch (err) {
		uni.showToast({ title: '加载失败', icon: 'none' });
	} finally {
		loading.value = false;
	}
};

const formatDate = (s) => {
	if (!s) return '待定';
	const d = new Date(s);
	if (Number.isNaN(d.getTime())) return s;
	return `${d.getMonth() + 1}月${d.getDate()}日`;
};

const goToAssignment = (item) => {
	uni.navigateTo({ url: `/pages/assignments/detail?id=${item.id}&courseId=${courseId.value}` });
};

const goToVideos = () => {
	uni.navigateTo({ url: `/pages/course/videos?courseId=${courseId.value}` });
};
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.loading,
.empty {
	padding: 100rpx 20rpx;
	text-align: center;
}

.loading-text,
.empty-text {
	font-size: 24rpx;
	color: #6d7b9b;
}

.course-card,
.section,
.assignment-card {
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 24rpx;
	box-shadow: 0 12rpx 26rpx rgba(24, 53, 114, 0.1);
}

.course-card {
	padding: 26rpx;
	margin-bottom: 16rpx;
}

.course-name {
	display: block;
	font-size: 34rpx;
	font-weight: 700;
	color: #1f2f53;
	margin-bottom: 10rpx;
}

.course-desc {
	display: block;
	font-size: 24rpx;
	line-height: 1.65;
	color: #5b6c90;
	margin-bottom: 16rpx;
}

.info-row {
	display: flex;
	align-items: center;
	margin-bottom: 10rpx;
}

.info-label {
	width: 92rpx;
	font-size: 22rpx;
	color: #70809f;
}

.info-val {
	font-size: 23rpx;
	font-weight: 600;
	color: #2a3a61;
}

.status-tag {
	display: inline-block;
	padding: 4rpx 14rpx;
	border-radius: 999rpx;
	font-size: 20rpx;
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

.section {
	padding: 24rpx;
	margin-bottom: 18rpx;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.section-header {
	padding: 4rpx 2rpx 14rpx;
}

.section-title {
	font-size: 30rpx;
	font-weight: 700;
	color: #1d2d50;
}

.section-arrow {
	font-size: 30rpx;
	color: #7b89a8;
}

.assignment-card {
	padding: 22rpx;
	margin-bottom: 16rpx;
}

.assignment-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10rpx;
}

.assignment-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1f2f53;
}

.assignment-desc {
	display: block;
	font-size: 23rpx;
	line-height: 1.6;
	color: #5f6f93;
	margin-bottom: 10rpx;
}

.assignment-deadline {
	font-size: 21rpx;
	font-weight: 600;
	color: #4e5f83;
}
</style>
