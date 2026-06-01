<template>
	<PageLayout>
		<view class="container">
			<view class="loading" v-if="loading"><text class="loading-text">正在加载提交记录...</text></view>

			<view class="empty" v-else-if="submissions.length === 0">
				<view class="empty-icon"><text class="empty-icon-text">□</text></view>
				<text class="empty-text">还没有提交记录</text>
			</view>

			<view v-else>
				<view class="submission-card" v-for="(item, idx) in submissions" :key="item.id" :class="{ latest: isLatest(idx) }">
					<view class="card-header">
						<text class="sub-title">{{ item.title }}</text>
						<view class="score-box">
							<text class="score" :class="item.score !== null ? 'scored' : 'pending'">
								{{ item.score !== null ? item.score + '分' : '待评分' }}
							</text>
						</view>
					</view>
					<text class="sub-time">提交时间: {{ formatDate(item.CREATE_TIME) }}</text>

					<view class="video-section" v-if="isLatest(idx) && item.content_url">
						<text class="feedback-label">AI 分析视频</text>
						<text class="video-hint">AI 处理后的视频请到网页端查看</text>
					</view>

					<view class="feedback-section" v-if="item.AI_feedback">
						<text class="feedback-label">AI 评语</text>
						<text class="feedback-content">{{ item.AI_feedback }}</text>
					</view>

					<view class="feedback-section" v-if="item.teacher_feedback">
						<text class="feedback-label">教师评语</text>
						<text class="feedback-content">{{ item.teacher_feedback }}</text>
					</view>

					<text class="latest-tag" v-if="isLatest(idx)">最新有效提交</text>
				</view>
			</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import request from '@/services/request';
import PageLayout from '@/components/PageLayout.vue';

const submissions = ref([]);
const loading = ref(true);
const assignmentId = ref('');
const courseId = ref('');

const getToken = () => {
	const token = uni.getStorageSync('token');
	if (token) return token;
	const user = uni.getStorageSync('user') || {};
	return user.token || '';
};

onMounted(() => {
	const pages = getCurrentPages();
	const page = pages[pages.length - 1];
	assignmentId.value = page.options?.assignmentId || '';
	courseId.value = page.options?.courseId || '';
	loadSubmissions();
});

const isLatest = (idx) => idx === submissions.value.length - 1;

const loadSubmissions = async () => {
	loading.value = true;
	const user = uni.getStorageSync('user') || {};
	const token = getToken();

	try {
		const resp = await request.post('/Homework/get_submit_id_by_student', {
			first: '0',
			second: user?.id,
			third: token,
			fourth: assignmentId.value || '1',
			fifth: user?.id
		});

		if (!resp.data?.success || !resp.data.data || resp.data.data === 'NULL') {
			submissions.value = [];
			return;
		}

		const ids = resp.data.data.split('\t\r').filter((i) => i.trim());
		const items = [];

		for (const sid of ids) {
			try {
				const infoResp = await request.post('/Homework/get_submit_info', {
					first: '0',
					second: user?.id,
					third: token,
					fourth: sid.trim()
				});

				if (infoResp.data?.success && infoResp.data.data) {
					const d = infoResp.data.data.split('\t\r');
					items.push({
						id: sid.trim(),
						content_url: d[0] || null,
						score: d[1] ? parseFloat(d[1]) : null,
						AI_feedback: d[2] || '',
						teacher_feedback: d[3] || '',
						CREATE_TIME: d[4] || ''
					});
				}
			} catch (e) {
				console.error('load submit item error', e);
			}
		}

		items.sort((a, b) => parseInt(a.id, 10) - parseInt(b.id, 10));
		items.forEach((s, i) => {
			s.title = `第${i + 1}次提交`;
		});
		submissions.value = items;
	} catch (e) {
		console.error('load submissions error', e);
		uni.showToast({ title: '加载失败', icon: 'none' });
	} finally {
		loading.value = false;
	}
};

const formatDate = (s) => {
	if (!s) return '-';
	const d = new Date(s);
	if (Number.isNaN(d.getTime())) return s;
	return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
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
	margin: 0 auto 14rpx;
	border-radius: 24rpx;
	background: #edf4ff;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #4d78d8;
}

.empty-icon-text {
	font-size: 44rpx;
	line-height: 1;
}

.submission-card {
	position: relative;
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 24rpx;
	padding: 24rpx;
	margin-bottom: 18rpx;
	box-shadow: 0 12rpx 26rpx rgba(24, 53, 114, 0.1);
}

.latest {
	border-color: rgba(18, 185, 129, 0.4);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10rpx;
}

.sub-title {
	font-size: 29rpx;
	font-weight: 700;
	color: #1f2f53;
}

.score {
	font-size: 30rpx;
	font-weight: 700;
}

.scored {
	color: #10a875;
}

.pending {
	color: #f08b12;
}

.sub-time {
	display: block;
	font-size: 22rpx;
	color: #6d7a98;
	margin-bottom: 12rpx;
}

.video-section {
	margin-bottom: 12rpx;
}

.video-hint {
	display: block;
	margin-top: 6rpx;
	font-size: 23rpx;
	line-height: 1.6;
	color: #6d7a98;
}

.feedback-section {
	background: #f5f8ff;
	border: 1rpx solid #e4eafd;
	border-radius: 14rpx;
	padding: 14rpx;
	margin-bottom: 10rpx;
}

.feedback-label {
	display: block;
	font-size: 22rpx;
	font-weight: 700;
	color: #2a3b63;
	margin-bottom: 6rpx;
}

.feedback-content {
	font-size: 23rpx;
	line-height: 1.65;
	color: #5b6b8f;
}

.latest-tag {
	display: inline-block;
	margin-top: 12rpx;
	padding: 4rpx 12rpx;
	border-radius: 999rpx;
	font-size: 20rpx;
	font-weight: 600;
	background: rgba(18, 185, 129, 0.12);
	color: #0f8a5f;
}
</style>
