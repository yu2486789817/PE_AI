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
				<text class="upload-hint">相册/拍摄支持 60 秒以内；长视频请先发到文件传输助手再选择</text>
				<button class="choose-btn" @click="chooseVideo" :disabled="assignment.statusClass === 'ended'">
					<text class="choose-btn-text">选择短视频</text>
				</button>
				<button class="file-btn" @click="chooseMessageVideo" :disabled="assignment.statusClass === 'ended'">
					<text class="choose-btn-text">选择长视频文件</text>
				</button>
				<text class="video-error" v-if="videoError">{{ videoError }}</text>

				<view class="file-info" v-if="selectedFile">
					<text class="file-name">{{ selectedFile.name }}</text>
					<text class="file-size">{{ formatSize(selectedFile.size) }}</text>
					<text class="remove-btn" @click="removeFile">移除</text>
				</view>

				<view class="progress-box" v-if="isUploading">
					<text class="progress-text">上传中... {{ uploadProgress }}%</text>
					<text class="progress-text" v-if="processingText">{{ processingText }}</text>
					<view class="progress-bar"><view class="progress-fill" :style="{ width: uploadProgress + '%' }"></view></view>
				</view>

				<button class="submit-btn" :disabled="!selectedFile || isUploading" @click="submitAssignment">
					<text class="submit-btn-text">{{ isUploading ? '上传中...' : '提交作业' }}</text>
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
const processingText = ref('');
const videoError = ref('');

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
			const deadline = d[2] || '';

			// 检查提交状态
			let statusText = '进行中';
			let statusClass = 'active';
			try {
				const user = uni.getStorageSync('user') || {};
				const token = uni.getStorageSync('token') || '';
				const submitResp = await request.post('/Homework/get_submit_id_by_student', {
					first: '0',
					second: user?.id,
					third: token,
					fourth: assignmentId.value,
					fifth: user?.id
				});
				if (submitResp.data?.success && submitResp.data?.data) {
					const submitData = submitResp.data.data.trim();
					const invalidValues = ['NULL', '-1', '-2', ''];
					if (!invalidValues.includes(submitData)) {
						statusText = '已完成';
						statusClass = 'active';
					} else if (deadline && new Date(deadline) < new Date()) {
						statusText = '已截止';
						statusClass = 'ended';
					}
				} else if (deadline && new Date(deadline) < new Date()) {
					statusText = '已截止';
					statusClass = 'ended';
				}
			} catch (e) {
				// 检查失败时 fallback 到截止日期判断
				if (deadline && new Date(deadline) < new Date()) {
					statusText = '已截止';
					statusClass = 'ended';
				}
			}

			assignment.value = {
				title: d[0] || `作业 ${assignmentId.value}`,
				description: d[1] || '',
				deadline: deadline,
				statusText: statusText,
				statusClass: statusClass
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
	videoError.value = '';

	const setSelectedVideo = (path, size = 0, name = '') => {
		if (!path) {
			videoError.value = '未获取到视频路径，请换一个视频再试。';
			uni.showToast({ title: videoError.value, icon: 'none' });
			return;
		}
		selectedFile.value = {
			path,
			name: name || path.split('/').pop() || '作业视频.mp4',
			size: size || 0
		};
	};

	uni.chooseVideo({
		sourceType: ['album', 'camera'],
		maxDuration: 60,
		success: (res) => setSelectedVideo(res.tempFilePath, res.size),
		fail: (err) => {
			if (err?.errMsg && err.errMsg.includes('cancel')) return;
			console.error('选择视频失败:', err);
			videoError.value = err?.errMsg || '无法打开视频选择器，请确认微信已授予相册/相机权限。';
			uni.showModal({
				title: '选择视频失败',
				content: videoError.value,
				showCancel: false
			});
		}
	});
};

const chooseMessageVideo = () => {
	videoError.value = '';

	if (!wx?.chooseMessageFile) {
		videoError.value = '当前微信版本不支持从聊天文件选择视频。';
		uni.showToast({ title: videoError.value, icon: 'none' });
		return;
	}

	wx.chooseMessageFile({
		count: 1,
		type: 'video',
		success: (res) => {
			const file = res.tempFiles?.[0] || {};
			if (!file.path) {
				videoError.value = '未获取到视频文件路径，请换一个文件再试。';
				uni.showToast({ title: videoError.value, icon: 'none' });
				return;
			}
			selectedFile.value = {
				path: file.path,
				name: file.name || file.path.split('/').pop() || '作业视频.mp4',
				size: file.size || 0
			};
		},
		fail: (err) => {
			if (err?.errMsg && err.errMsg.includes('cancel')) return;
			console.error('选择长视频文件失败:', err);
			videoError.value = err?.errMsg || '选择长视频文件失败，请先把视频发到文件传输助手。';
			uni.showModal({
				title: '选择长视频失败',
				content: videoError.value,
				showCancel: false
			});
		}
	});
};

const submitAssignment = async () => {
	if (!selectedFile.value) return;
	isUploading.value = true;
	uploadProgress.value = 0;
	processingText.value = '准备压缩视频...';
	const user = uni.getStorageSync('user') || {};
	const studentId = user?.id || '';
	const jwt = uni.getStorageSync('token') || user?.token || '';

	const uploadProgressTimer = setInterval(() => {
		if (uploadProgress.value < 90) uploadProgress.value += 5;
	}, 400);

	try {
		if (!studentId) throw new Error('未获取到学生ID');

		const compressed = await compressVideo(selectedFile.value.path);
		processingText.value = '正在上传视频，AI分析将在后台进行...';

		const submitResp = await uploadHomeworkVideo(compressed.path, {
			student_id: studentId,
			course_id: courseId.value,
			homework_id: assignmentId.value,
			pose_type: aiType.value || 'pushup'
		});

		if (!submitResp?.data?.success) {
			throw new Error(submitResp?.data?.message || '提交失败');
		}

		uploadProgress.value = 100;
		uni.showToast({ title: '提交成功，AI后台分析中' });
		selectedFile.value = null;
		if (assignment.value) {
			assignment.value.statusText = '已提交';
			assignment.value.statusClass = 'active';
		}
	} catch (e) {
		const message = e?.message || '提交失败';
		uni.showModal({
			title: '提交失败',
			content: message,
			showCancel: false
		});
	} finally {
		clearInterval(uploadProgressTimer);
		isUploading.value = false;
		processingText.value = '';
	}
};

const compressVideo = (src) => {
	return new Promise((resolve, reject) => {
		if (!uni.compressVideo) {
			resolve({ path: src, size: selectedFile.value?.size || 0 });
			return;
		}
		uni.compressVideo({
			src,
			quality: 'medium',
			success: (res) => {
				resolve({
					path: res.tempFilePath,
					size: res.size || 0
				});
			},
			fail: (err) => {
				// 压缩失败则回退原视频，避免阻断提交流程
				resolve({ path: src, size: 0 });
			}
		});
	});
};

const uploadHomeworkVideo = (filePath, formData) => {
	return new Promise((resolve, reject) => {
		uni.uploadFile({
			url: request.buildURL('/Homework/upload_submit'),
			filePath,
			name: 'file',
			formData,
			timeout: 120000,
			header: {
				Authorization: `Bearer ${uni.getStorageSync('token') || ''}`
			},
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					if (typeof res.data === 'string') {
						try {
							res.data = JSON.parse(res.data);
						} catch (e) {
							reject(new Error('提交响应解析失败'));
							return;
						}
					}
					resolve(res);
					return;
				}
				reject(new Error(`上传失败(${res.statusCode})：${res.data || '服务器未返回详细信息'}`));
			},
			fail: (err) => {
				console.error('上传作业视频失败:', err);
				reject(new Error(err?.errMsg || '上传失败，请检查 uploadFile 合法域名或网络'));
			}
		});
	});
};

const fetchAiStats = async (homeworkId, studentId, poseType) => {
	try {
		const resp = await request.get(
			`/video/query_records?homework_id=${encodeURIComponent(homeworkId)}&student_id=${encodeURIComponent(studentId)}&pose_type=${encodeURIComponent(poseType)}`
		);
		const rows = Array.isArray(resp?.data) ? resp.data : [];
		return rows.length > 0 ? rows[0] : null;
	} catch (e) {
		return null;
	}
};

const buildAiFeedback = (stats) => {
	if (!stats) return '';
	const total = Number(stats.total_count) || 0;
	const correct = Number(stats.correct_count) || 0;
	const incorrect = Number(stats.incorrect_count) || 0;
	if (total > 0) {
		const rate = Math.round((correct / total) * 100);
		return `本次动作共完成${total}次，其中标准${correct}次，不标准${incorrect}次，标准率${rate}%。`;
	}
	return '';
};

const removeFile = () => {
	selectedFile.value = null;
	videoError.value = '';
	uploadProgress.value = 0;
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

.choose-btn,
.file-btn {
	background: #f0f4ff;
	color: #255ad8;
}

.file-btn {
	margin-top: 12rpx;
}

.choose-btn[disabled],
.file-btn[disabled] {
	background: #edf2fb;
	color: #8a96ad;
	opacity: 1;
}

.video-error {
	display: block;
	margin-top: 12rpx;
	font-size: 22rpx;
	line-height: 1.5;
	color: #d93025;
}

.submit-btn {
	margin-top: 20rpx;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	color: #fff;
	box-shadow: 0 10rpx 22rpx rgba(29, 99, 255, 0.3);
}

.submit-btn[disabled] {
	background: linear-gradient(120deg, #9fbff8 0%, #a8d6fb 100%);
	color: #fff;
	opacity: 1;
}

.choose-btn-text,
.submit-btn-text {
	font-size: 27rpx;
	font-weight: 600;
	line-height: 82rpx;
	color: inherit;
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
