<template>
	<PageLayout>
		<view class="container">
		<view class="loading" v-if="loading"><text class="loading-text">正在加载提交记录...</text></view>

		<view class="empty" v-else-if="submissions.length === 0">
			<view class="empty-icon text-blue">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">
					<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
					<polyline points="22,6 12,13 2,6"></polyline>
				</svg>
			</view>
			<text class="empty-text">还没有提交记录</text>
		</view>

		<view v-else>
			<view class="submission-card" v-for="(item, idx) in submissions" :key="item.id" :class="{ latest: idx === submissions.length - 1 }">
				<view class="card-header">
					<text class="sub-title">{{ item.title }}</text>
					<view class="score-box">
						<text class="score" :class="item.score !== null ? 'scored' : 'pending'">
							{{ item.score !== null ? item.score + '分' : '待评分' }}
						</text>
					</view>
				</view>
				<text class="sub-time">提交时间: {{ formatDate(item.CREATE_TIME) }}</text>

				<view class="feedback-section" v-if="item.AI_feedback">
					<text class="feedback-label">AI 评语</text>
					<text class="feedback-content">{{ item.AI_feedback }}</text>
				</view>

				<view class="feedback-section" v-if="item.teacher_feedback">
					<text class="feedback-label">教师评语</text>
					<text class="feedback-content">{{ item.teacher_feedback }}</text>
				</view>

				<text class="latest-tag" v-if="idx === submissions.length - 1">最新有效提交</text>
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

onMounted(() => {
	const pages = getCurrentPages();
	const page = pages[pages.length - 1];
	assignmentId.value = page.options?.assignmentId || '';
	loadSubmissions();
});

const loadSubmissions = async () => {
	loading.value = true;
	const user = uni.getStorageSync('user');
	const token = uni.getStorageSync('token');

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
			loading.value = false;
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
				// ignore one broken submit item
			}
		}

		items.sort((a, b) => parseInt(a.id, 10) - parseInt(b.id, 10));
		items.forEach((s, i) => {
			s.title = `第 ${i + 1} 次提交`;
		});
		submissions.value = items;
	} catch (e) {
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
	color: var(--ink-500);
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
	position: absolute;
	top: 18rpx;
	right: 18rpx;
	padding: 4rpx 12rpx;
	border-radius: 999rpx;
	font-size: 20rpx;
	font-weight: 600;
	background: rgba(18, 185, 129, 0.12);
	color: #0f8a5f;
}
</style>
