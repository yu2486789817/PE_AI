<template>
	<PageLayout>
		<view class="container">
		<view class="loading" v-if="loading"><text class="loading-text">正在加载教学视频...</text></view>

		<view class="empty" v-else-if="videos.length === 0">
			<view class="empty-icon text-blue">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">
					<polygon points="23 7 16 12 23 17 23 7"></polygon>
					<rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
				</svg>
			</view>
			<text class="empty-text">暂无教学视频</text>
		</view>

		<view v-else>
			<view class="video-card" v-for="video in videos" :key="video.id" @click="playVideo(video)">
				<view class="video-cover"><text class="play-icon">▶</text></view>
				<view class="video-info">
					<text class="video-title">{{ video.title }}</text>
					<text class="video-desc">{{ video.description }}</text>
					<text class="video-date">{{ formatDate(video.create_time) }}</text>
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

const videos = ref([]);
const loading = ref(true);
const courseId = ref('');

onMounted(() => {
	const pages = getCurrentPages();
	const page = pages[pages.length - 1];
	courseId.value = page.options?.courseId || '';
	loadVideos();
});

const loadVideos = async () => {
	loading.value = true;
	const user = uni.getStorageSync('user') || {};
	const token = uni.getStorageSync('token') || user?.token || '';
	try {
		const idResp = await request.post('/Class/get_class_id_by_course', {
			first: '0',
			second: user?.id,
			third: token,
			fourth: courseId.value
		});

		if (!idResp.data?.success || !idResp.data?.data || idResp.data.data === 'NULL') {
			videos.value = [];
			loading.value = false;
			return;
		}

		const ids = idResp.data.data.split('\t\r').filter((i) => i.trim());
		const items = [];
		for (const cid of ids) {
			try {
				const infoResp = await request.post('/Class/get_info_by_class_id', {
					first: courseId.value,
					second: cid
				});
				if (infoResp.data?.success && infoResp.data?.data) {
					const d = infoResp.data.data.split('\t\r');
					const rawUrl = d[2] || '';
					const filename = rawUrl ? rawUrl.substring(rawUrl.lastIndexOf('/') + 1) : '';
					const normalizedUrl = filename ? `/Teaching-video/files/${filename}` : '';
					items.push({
						id: cid,
						title: d[0] || '未命名视频',
						description: d[1] || '',
						url: normalizedUrl || rawUrl,
						create_time: d[3] || ''
					});
				}
			} catch (e) {
				console.error('load class video info error', e);
			}
		}
		videos.value = items;
	} catch (e) {
		uni.showToast({ title: '加载失败', icon: 'none' });
	} finally {
		loading.value = false;
	}
};

const playVideo = (video) => {
	let url = video.url;
	if (url && url.includes('localhost:5002')) {
		const filename = url.substring(url.lastIndexOf('/') + 1);
		url = `/Teaching-video/files/${filename}`;
	}

	uni.navigateTo({ url: `/pages/course/videoPlayer?url=${encodeURIComponent(url)}&title=${encodeURIComponent(video.title)}` });
};

const formatDate = (s) => {
	if (!s) return '-';
	const d = new Date(s);
	if (Number.isNaN(d.getTime())) return s;
	return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
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

.video-card {
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 24rpx;
	overflow: hidden;
	margin-bottom: 18rpx;
	box-shadow: 0 12rpx 26rpx rgba(24, 53, 114, 0.1);
}

.video-cover {
	height: 240rpx;
	background: linear-gradient(130deg, #1a57e8 0%, #2f86ff 45%, #18bcff 100%);
	display: flex;
	align-items: center;
	justify-content: center;
}

.play-icon {
	font-size: 72rpx;
	color: rgba(255, 255, 255, 0.95);
}

.video-info {
	padding: 20rpx;
}

.video-title {
	display: block;
	font-size: 28rpx;
	font-weight: 700;
	line-height: 1.4;
	color: #1f2f53;
	margin-bottom: 8rpx;
}

.video-desc {
	display: block;
	font-size: 23rpx;
	line-height: 1.6;
	color: #5f6f93;
	margin-bottom: 10rpx;
}

.video-date {
	font-size: 21rpx;
	font-weight: 600;
	color: #4f6083;
}
</style>
