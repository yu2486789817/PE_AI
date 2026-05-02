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
						<video :src="item.content_url" class="video-player" controls object-fit="contain"></video>
						<button class="mini-btn" @click="openVideoPlayer(item)">全屏播放</button>
					</view>

					<view class="feedback-section" v-if="item.AI_feedback">
						<text class="feedback-label">AI 评语</text>
						<text class="feedback-content">{{ item.AI_feedback }}</text>
					</view>

					<view class="feedback-section" v-if="item.teacher_feedback">
						<text class="feedback-label">教师评语</text>
						<text class="feedback-content">{{ item.teacher_feedback }}</text>
					</view>

					<view class="action-row" v-if="isLatest(idx)">
						<button class="action-btn primary" @click="openReportDialog(item)">生成AI报告</button>
						<button class="action-btn" @click="downloadReport(item)">下载报告</button>
						<button class="action-btn danger" v-if="item.content_url" @click="deleteVideo(item)">删除视频</button>
					</view>

					<text class="latest-tag" v-if="isLatest(idx)">最新有效提交</text>
				</view>
			</view>

			<view class="mask" v-if="showReportDialog" @click="closeReportDialog">
				<view class="dialog" @click.stop>
					<view class="dialog-header">
						<text class="dialog-title">AI 分析报告</text>
						<text class="dialog-close" @click="closeReportDialog">×</text>
					</view>
					<text class="dialog-sub">{{ currentSubmission && currentSubmission.title ? currentSubmission.title : '' }}</text>

					<textarea
						class="dialog-input"
						v-model="reportQuery"
						auto-height
						maxlength="500"
						placeholder="请输入希望 AI 重点分析的问题，例如：动作规范度、节奏控制、改进建议。"
					/>

					<button class="dialog-generate" :disabled="reportLoading || !reportQuery.trim()" @click="generateAnalysisReport">
						{{ reportLoading ? '生成中...' : '生成AI分析报告' }}
					</button>

					<view v-if="reportError" class="dialog-error">
						<text class="dialog-error-text">{{ reportError }}</text>
					</view>

					<scroll-view scroll-y class="dialog-report" v-if="reportContent">
						<text class="dialog-report-text">{{ reportContent }}</text>
					</scroll-view>

					<view class="dialog-actions">
						<button class="dialog-btn" v-if="reportContent" @click="downloadCurrentReport">下载报告</button>
						<button class="dialog-btn cancel" @click="closeReportDialog">关闭</button>
					</view>
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

const showReportDialog = ref(false);
const currentSubmission = ref(null);
const reportQuery = ref('');
const reportContent = ref('');
const reportError = ref('');
const reportLoading = ref(false);

const getToken = () => {
	const token = uni.getStorageSync('token');
	if (token) return token;
	const user = uni.getStorageSync('user') || {};
	return user.token || '';
};

const getDateKey = () => {
	const now = new Date();
	const y = now.getFullYear();
	const m = String(now.getMonth() + 1).padStart(2, '0');
	const d = String(now.getDate()).padStart(2, '0');
	return `${y}-${m}-${d}`;
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

const openVideoPlayer = (item) => {
	if (!item?.content_url) return;
	const url = encodeURIComponent(item.content_url);
	const title = encodeURIComponent(item.title || 'AI分析视频');
	uni.navigateTo({ url: `/pages/course/videoPlayer?url=${url}&title=${title}` });
};

const openReportDialog = (item) => {
	currentSubmission.value = item;
	reportQuery.value = '请详细分析本次作业表现，并给出改进建议和下一步训练计划。';
	reportContent.value = '';
	reportError.value = '';
	showReportDialog.value = true;
};

const closeReportDialog = () => {
	if (reportLoading.value) return;
	showReportDialog.value = false;
};

const generateAnalysisReport = async () => {
	const item = currentSubmission.value;
	const user = uni.getStorageSync('user') || {};
	if (!item || !user?.id || !reportQuery.value.trim()) return;

	reportLoading.value = true;
	reportError.value = '';
	reportContent.value = '';
	try {
		const reportResp = await request.post('/chat/api/analysis/generate', {
			student_id: user.id,
			analysis_type: 'homework_feedback',
			homework_id: assignmentId.value,
			query: reportQuery.value.trim()
		});

		if (!reportResp.data?.success || !reportResp.data?.data?.report) {
			throw new Error(reportResp.data?.error || '报告生成失败');
		}

		const report = reportResp.data.data.report;
		reportContent.value = report;
		item.AI_feedback = report;

		await request.post('/Homework/AI_test', {
			first: String(item.id),
			second: item.content_url || '',
			third: item.score !== null ? String(item.score) : '0',
			fourth: report
		});

		uni.showToast({ title: '报告已生成', icon: 'success' });
	} catch (e) {
		reportError.value = e?.message || '生成失败';
	} finally {
		reportLoading.value = false;
	}
};

const downloadText = (content, fileName) => {
	// #ifdef H5
	const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = fileName;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
	// #endif

	// #ifndef H5
	uni.setClipboardData({
		data: content,
		success: () => uni.showToast({ title: '已复制报告内容', icon: 'none' })
	});
	// #endif
};

const downloadReport = (item) => {
	const report = item?.AI_feedback || '';
	if (!report) {
		uni.showToast({ title: '暂无可下载报告', icon: 'none' });
		return;
	}
	downloadText(report, `AI分析报告_${item.id}_${getDateKey()}.md`);
};

const downloadCurrentReport = () => {
	if (!reportContent.value || !currentSubmission.value) return;
	downloadText(reportContent.value, `${currentSubmission.value.title || 'AI分析报告'}_${getDateKey()}.md`);
};

const confirmDelete = () => {
	return new Promise((resolve) => {
		uni.showModal({
			title: '删除视频',
			content: '确认删除该次提交的 AI 分析视频吗？',
			success: (res) => resolve(!!res.confirm),
			fail: () => resolve(false)
		});
	});
};

const deleteVideo = async (item) => {
	const ok = await confirmDelete();
	if (!ok) return;

	try {
		const resp = await request.delete(`/video/delete_homework?homework_id=${encodeURIComponent(item.id)}`);
		const data = resp?.data || {};
		if (data.success || data.status === 'success') {
			item.content_url = '';
			uni.showToast({ title: '删除成功', icon: 'success' });
			return;
		}
		throw new Error(data.message || data.detail || '删除失败');
	} catch (e) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
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

.video-section {
	margin-bottom: 12rpx;
}

.video-player {
	width: 100%;
	height: 360rpx;
	border-radius: 14rpx;
	background: #000;
}

.mini-btn {
	margin-top: 10rpx;
	height: 62rpx;
	line-height: 62rpx;
	border-radius: 999rpx;
	font-size: 23rpx;
	font-weight: 600;
	background: #eef2ff;
	color: #33539a;
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

.action-row {
	display: flex;
	gap: 12rpx;
	margin-top: 10rpx;
	flex-wrap: wrap;
}

.action-btn {
	flex: 1;
	height: 72rpx;
	line-height: 72rpx;
	border-radius: 999rpx;
	background: #eef2ff;
	color: #334;
	font-size: 24rpx;
	font-weight: 600;
	min-width: 180rpx;
}

.action-btn.primary {
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	color: #fff;
}

.action-btn.danger {
	background: #ffe9ea;
	color: #c43f3f;
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

.mask {
	position: fixed;
	inset: 0;
	background: rgba(10, 20, 40, 0.45);
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24rpx;
	z-index: 999;
}

.dialog {
	width: 100%;
	max-height: 86vh;
	background: #fff;
	border-radius: 24rpx;
	padding: 24rpx;
	display: flex;
	flex-direction: column;
}

.dialog-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.dialog-title {
	font-size: 30rpx;
	font-weight: 700;
	color: #1f2f53;
}

.dialog-close {
	font-size: 44rpx;
	line-height: 1;
	color: #7b879f;
}

.dialog-sub {
	margin-top: 8rpx;
	font-size: 23rpx;
	color: #7381a1;
}

.dialog-input {
	margin-top: 16rpx;
	min-height: 120rpx;
	max-height: 260rpx;
	padding: 14rpx;
	border-radius: 12rpx;
	font-size: 24rpx;
	line-height: 1.6;
	background: #f6f9ff;
	border: 1rpx solid #dfe7fb;
}

.dialog-generate {
	margin-top: 12rpx;
	height: 74rpx;
	line-height: 74rpx;
	border-radius: 999rpx;
	font-size: 24rpx;
	font-weight: 600;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	color: #fff;
}

.dialog-generate[disabled] {
	opacity: 0.55;
}

.dialog-error {
	margin-top: 12rpx;
	padding: 12rpx;
	border-radius: 10rpx;
	background: #ffe9ea;
}

.dialog-error-text {
	font-size: 22rpx;
	color: #bf3d3d;
}

.dialog-report {
	margin-top: 12rpx;
	max-height: 320rpx;
	padding: 14rpx;
	border-radius: 12rpx;
	background: #f8faff;
	border: 1rpx solid #e2e9fc;
}

.dialog-report-text {
	font-size: 23rpx;
	line-height: 1.7;
	color: #42557f;
	white-space: pre-wrap;
}

.dialog-actions {
	display: flex;
	gap: 12rpx;
	margin-top: 16rpx;
}

.dialog-btn {
	flex: 1;
	height: 72rpx;
	line-height: 72rpx;
	border-radius: 999rpx;
	font-size: 24rpx;
	font-weight: 600;
	background: #eaf0ff;
	color: #33539a;
}

.dialog-btn.cancel {
	background: #f2f3f7;
	color: #5d6781;
}
</style>
