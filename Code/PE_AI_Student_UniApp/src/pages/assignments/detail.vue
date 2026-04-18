<template>
	<PageLayout>
		<view class="container">
		<view class="loading" v-if="loading"><text class="loading-text">正在加载作业详情...</text></view>

		<view v-else-if="assignment" class="detail-box">
			<text class="hw-title">{{ assignment.title }}</text>

			<view class="meta-grid">
				<view class="meta-item">
					<text class="meta-label">截止时间</text>
					<text class="meta-val">{{ formatDate(assignment.deadline) }}</text>
				</view>
				<view class="meta-item">
					<text class="meta-label">状态</text>
					<text :class="['status-tag', assignment.statusClass]">{{ assignment.statusText }}</text>
				</view>
				<view class="meta-item">
					<text class="meta-label">动作类型</text>
					<text class="meta-val">{{ aiType || '加载中...' }}</text>
				</view>
				<view class="meta-item">
					<text class="meta-label">要求数量</text>
					<text class="meta-val">{{ requiredCount !== null ? requiredCount : '加载中...' }}</text>
				</view>
			</view>

			<view class="desc-box">
				<text class="desc-title">作业描述</text>
				<text class="desc-content">{{ assignment.description }}</text>
			</view>

			<view class="ai-hint">
				<text class="ai-hint-title">AI 评分说明</text>
				<text class="ai-hint-text">提交视频后，系统会自动评估动作规范度、完成度与关键技术点，并给出反馈。</text>
			</view>

			<view class="upload-box">
				<text class="upload-title">上传作业视频</text>
				<text class="upload-hint">支持 MP4 格式，建议 300 秒以内</text>
				<button class="choose-btn" @click="chooseVideo" :disabled="assignment.statusClass === 'ended'">选择视频文件</button>

				<view class="file-info" v-if="selectedFile">
					<text class="file-name">{{ selectedFile.name }}</text>
					<text class="file-size">{{ formatSize(selectedFile.size) }}</text>
					<text class="remove-btn" @click="removeFile">移除</text>
				</view>

				<view class="progress-box" v-if="isUploading">
					<text class="progress-text">上传中... {{ uploadProgress }}%</text>
					<view class="progress-bar"><view class="progress-fill" :style="{ width: uploadProgress + '%' }"></view></view>
				</view>

				<button class="submit-btn" :disabled="!selectedFile || isUploading" @click="submitAssignment">
					{{ isUploading ? '上传中...' : '提交作业' }}
				</button>
			</view>

			<button class="history-btn" @click="goToHistory">查看提交历史</button>
		</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import request from '@/services/request';
import PageLayout from '@/components/PageLayout.vue';

const assignment = ref(null);
const loading = ref(true);
const aiType = ref(null);
const requiredCount = ref(null);
const selectedFile = ref(null);
const isUploading = ref(false);
const uploadProgress = ref(0);
const assignmentId = ref('');
const courseId = ref('');

onMounted(() => {
	const pages = getCurrentPages();
	const page = pages[pages.length - 1];
	assignmentId.value = page.options?.id || '';
	courseId.value = page.options?.courseId || '';
	loadAssignment();
});

const loadAssignment = async () => {
	loading.value = true;
	try {
		const resp = await request.post('/Homework/get_info_by_homework_id', {
			first: courseId.value,
			second: assignmentId.value
		});

		if (resp.data?.success && resp.data.data) {
			const d = resp.data.data.split('\t\r');
			const isActive = d[2] && new Date(d[2]) > new Date();
			assignment.value = {
				title: d[0] || `作业 ${assignmentId.value}`,
				description: d[1] || '',
				deadline: d[2] || '',
				statusText: isActive ? '进行中' : '已截止',
				statusClass: isActive ? 'active' : 'ended'
			};
		}

		try {
			const poseResp = await request.post('/Homework/get_AI_type', { first: assignmentId.value });
			if (poseResp.data?.success && poseResp.data.data) {
				const pd = poseResp.data.data.split('\t\r');
				aiType.value = pd[0] || '未知';
				requiredCount.value = pd[1] || 0;
			}
		} catch (e) {
			aiType.value = '未配置';
		}
	} catch (e) {
		uni.showToast({ title: '作业加载失败', icon: 'none' });
	} finally {
		loading.value = false;
	}
};

const chooseVideo = () => {
	uni.chooseVideo({
		sourceType: ['album', 'camera'],
		maxDuration: 300,
		success: (res) => {
			selectedFile.value = {
				path: res.tempFilePath,
				name: res.tempFilePath.split('/').pop(),
				size: res.size || 0
			};
		}
	});
};

const removeFile = () => {
	selectedFile.value = null;
};

const submitAssignment = async () => {
	if (!selectedFile.value) return;
	isUploading.value = true;
	uploadProgress.value = 0;
	const user = uni.getStorageSync('user');

	try {
		uni.uploadFile({
			url: '/Homework/upload_homework',
			filePath: selectedFile.value.path,
			name: 'video',
			formData: {
				first: assignmentId.value,
				second: user?.id || ''
			},
			success: () => {
				uni.showToast({ title: '提交成功' });
				if (assignment.value) {
					assignment.value.statusText = '已提交';
					assignment.value.statusClass = 'active';
				}
			},
			fail: () => {
				uni.showToast({ title: '提交失败', icon: 'none' });
			},
			complete: () => {
				isUploading.value = false;
			}
		});

		const timer = setInterval(() => {
			if (uploadProgress.value < 90) uploadProgress.value += 10;
			else clearInterval(timer);
		}, 500);
	} catch (e) {
		isUploading.value = false;
		uni.showToast({ title: '提交失败', icon: 'none' });
	}
};

const formatDate = (s) => {
	if (!s) return '待定';
	const d = new Date(s);
	if (Number.isNaN(d.getTime())) return s;
	return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

const formatSize = (bytes) => {
	if (!bytes) return '';
	const k = 1024;
	const units = ['B', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
};

const goToHistory = () => {
	uni.navigateTo({ url: `/pages/assignments/history?courseId=${courseId.value}&assignmentId=${assignmentId.value}` });
};
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.loading {
	padding: 100rpx 0;
	text-align: center;
}

.loading-text {
	font-size: 24rpx;
	color: #6d7b9b;
}

.detail-box {
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 28rpx;
	padding: 28rpx;
	box-shadow: 0 14rpx 30rpx rgba(24, 52, 113, 0.1);
}

.hw-title {
	display: block;
	font-size: 34rpx;
	font-weight: 700;
	line-height: 1.4;
	color: #1d2d50;
	margin-bottom: 20rpx;
}

.meta-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12rpx;
	margin-bottom: 20rpx;
}

.meta-item {
	background: #f4f7ff;
	border: 1rpx solid #e2eaff;
	border-radius: 16rpx;
	padding: 12rpx 14rpx;
}

.meta-label {
	display: block;
	font-size: 21rpx;
	color: #7380a0;
}

.meta-val {
	display: block;
	margin-top: 6rpx;
	font-size: 24rpx;
	font-weight: 600;
	color: #203055;
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

.desc-box,
.ai-hint {
	border-radius: 16rpx;
	padding: 18rpx;
	margin-bottom: 18rpx;
}

.desc-box {
	background: rgba(29, 99, 255, 0.08);
	border: 1rpx solid rgba(29, 99, 255, 0.16);
}

.ai-hint {
	background: rgba(24, 183, 255, 0.09);
	border: 1rpx solid rgba(24, 183, 255, 0.2);
}

.desc-title,
.ai-hint-title {
	display: block;
	font-size: 25rpx;
	font-weight: 700;
	color: #1f2f54;
	margin-bottom: 8rpx;
}

.desc-content,
.ai-hint-text {
	font-size: 23rpx;
	line-height: 1.7;
	color: #506186;
}

.upload-box {
	margin-top: 14rpx;
}

.upload-title {
	display: block;
	font-size: 28rpx;
	font-weight: 700;
	color: #1e2d50;
	margin-bottom: 4rpx;
}

.upload-hint {
	display: block;
	font-size: 22rpx;
	color: #6d7b9a;
	margin-bottom: 14rpx;
}

.choose-btn,
.submit-btn,
.history-btn {
	height: 82rpx;
	line-height: 82rpx;
	font-size: 27rpx;
	font-weight: 600;
	border-radius: 999rpx;
}

.choose-btn {
	background: #f0f4ff;
	color: #255ad8;
}

.submit-btn {
	margin-top: 20rpx;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	color: #fff;
	box-shadow: 0 10rpx 22rpx rgba(29, 99, 255, 0.3);
}

.history-btn {
	margin-top: 14rpx;
	background: #f0f4ff;
	color: #36558f;
}

.file-info {
	background: #f6f8ff;
	border: 1rpx solid #e3eafe;
	border-radius: 14rpx;
	padding: 14rpx;
	margin-top: 14rpx;
}

.file-name {
	display: block;
	font-size: 24rpx;
	font-weight: 600;
	color: #24365d;
}

.file-size {
	font-size: 21rpx;
	color: #6b7998;
}

.remove-btn {
	font-size: 21rpx;
	font-weight: 600;
	color: #e53935;
	margin-left: 16rpx;
}

.progress-box {
	margin-top: 14rpx;
}

.progress-text {
	display: block;
	font-size: 22rpx;
	font-weight: 600;
	color: #2a61da;
	margin-bottom: 8rpx;
}

.progress-bar {
	height: 10rpx;
	background: #e4e9f7;
	border-radius: 999rpx;
	overflow: hidden;
}

.progress-fill {
	height: 100%;
	background: linear-gradient(90deg, #1d63ff 0%, #23b9ff 100%);
	border-radius: 999rpx;
	transition: width 0.3s ease;
}
</style>
