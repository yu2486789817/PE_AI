<template>
	<PageLayout>
		<view class="container">
		<view class="loading" v-if="loading"><text class="loading-text">正在加载教学视频...</text></view>

		<view class="empty" v-else-if="videos.length === 0">
			<view class="empty-icon"><text class="empty-icon-text">▶</text></view>
			<text class="empty-text">暂无教学视频</text>
		</view>

		<view v-else>
			<view class="video-card" v-for="(video, idx) in videos" :key="video.id" @click="playVideo(video)">
				<view class="video-cover">
					<video
						v-if="video.url"
						class="cover-video"
						:src="video.url"
						:controls="false"
						:show-center-play-btn="false"
						:show-play-btn="false"
						:enable-progress-gesture="false"
						object-fit="cover"
						:initial-time="0.5"
						@loadedmetadata="onMeta($event, idx)"
					></video>
					<view class="cover-mask"></view>
					<text class="play-icon">▶</text>
					<text class="duration-badge" v-if="video.duration">{{ video.duration }}</text>
				</view>
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

const resolveVideoUrl = (rawUrl) => {
	if (!rawUrl) return '';
	// 旧的本机文件服务器链接：改写为走后端文件接口
	if (rawUrl.includes('localhost:5002') || rawUrl.includes('47.121.177.100:5002')) {
		const filename = rawUrl.substring(rawUrl.lastIndexOf('/') + 1);
		return request.buildURL(`/Teaching-video/files/${filename}`);
	}
	// 已是完整 URL（如 Supabase 直链），小程序无法跟随 302，需直接使用
	if (/^https?:\/\//i.test(rawUrl)) {
		return rawUrl;
	}
	// 后端相对路径：拼成完整地址
	const filename = rawUrl.substring(rawUrl.lastIndexOf('/') + 1);
	return request.buildURL(`/Teaching-video/files/${filename}`);
};

const loadVideos = async () => {
	loading.value = true;
	const user = uni.getStorageSync('user') || {};
	const token = uni.getStorageSync('token') || user?.token || '';
	try {
		const idResp = await request.post('/Class/get_class_id_by_course', {
			capacity: '0',
			user_id: user?.id,
			jwt: token,
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
					second: cid,
					jwt: token
				});
				if (infoResp.data?.success && infoResp.data?.data) {
					const d = infoResp.data.data.split('\t\r');
					const rawUrl = d[2] || '';
					items.push({
						id: cid,
						title: d[0] || '未命名视频',
						description: d[1] || '',
						url: resolveVideoUrl(rawUrl),
						duration: '',
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
	const url = resolveVideoUrl(video.url);

	uni.navigateTo({ url: `/pages/course/videoPlayer?url=${encodeURIComponent(url)}&title=${encodeURIComponent(video.title)}` });
};

// <video> 元数据加载完成，回填真实时长
const onMeta = (e, idx) => {
	const dur = e?.detail?.duration;
	if (!dur || Number.isNaN(dur) || !videos.value[idx]) return;
	const mins = String(Math.floor(dur / 60)).padStart(2, '0');
	const secs = String(Math.floor(dur % 60)).padStart(2, '0');
	videos.value[idx].duration = `${mins}:${secs}`;
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
	border-radius: 24rpx;
	background: #edf4ff;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #4d78d8;
}

.empty-icon-text {
	font-size: 42rpx;
	line-height: 1;
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
	position: relative;
	height: 240rpx;
	background: linear-gradient(130deg, #1a57e8 0%, #2f86ff 45%, #18bcff 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
}

.cover-video {
	position: absolute;
	inset: 0;
	width: 100%;
	height: 100%;
}

.cover-mask {
	position: absolute;
	inset: 0;
	background: rgba(0, 0, 0, 0.18);
}

.play-icon {
	position: relative;
	z-index: 2;
	font-size: 72rpx;
	color: rgba(255, 255, 255, 0.95);
	text-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.35);
}

.duration-badge {
	position: absolute;
	right: 16rpx;
	bottom: 16rpx;
	z-index: 2;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
	background: rgba(0, 0, 0, 0.6);
	color: #fff;
	font-size: 20rpx;
	line-height: 1.4;
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
