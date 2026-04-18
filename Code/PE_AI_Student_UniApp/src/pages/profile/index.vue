<template>
	<PageLayout>
		<view class="container">
		<view class="user-header">
			<view class="avatar-box"><text class="avatar-text">{{ userInitial }}</text></view>
			<view class="user-info">
				<text class="user-name">{{ user.name || '未登录' }}</text>
				<text class="user-role">学生 · {{ user.id || '-' }}</text>
			</view>
		</view>

		<view class="info-card">
			<text class="card-title">账号详情</text>
			<view class="info-row"><text class="info-label">学号</text><text class="info-val">{{ user.id || '-' }}</text></view>
			<view class="info-row"><text class="info-label">姓名</text><text class="info-val">{{ user.name || '-' }}</text></view>
			<view class="info-row"><text class="info-label">性别</text><text class="info-val">{{ user.gender || '-' }}</text></view>
			<view class="info-row"><text class="info-label">专业</text><text class="info-val">{{ user.major || '-' }}</text></view>
			<view class="info-row"><text class="info-label">学院</text><text class="info-val">{{ user.college || '-' }}</text></view>
			<view class="info-row"><text class="info-label">系别</text><text class="info-val">{{ user.department || '-' }}</text></view>
		</view>

		<view class="menu-list">
			<view class="menu-item" @click="goTo('/pages/profile/edit')">
				<view class="menu-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%; color: var(--brand-500);">
						<path d="M12 20h9"></path>
						<path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
					</svg>
				</view>
				<text class="menu-text">编辑个人信息</text>
				<text class="arrow">></text>
			</view>
			<view class="menu-item" @click="goTo('/pages/profile/password')">
				<view class="menu-icon">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%; color: var(--brand-500);">
						<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
						<path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
					</svg>
				</view>
				<text class="menu-text">修改密码</text>
				<text class="arrow">></text>
			</view>
		</view>

		<button class="logout-btn" @click="handleLogout">退出登录</button>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { logout, getStudentInfo } from '@/services/auth';
import PageLayout from '@/components/PageLayout.vue';

const user = ref({});

const userInitial = computed(() => {
	const name = user.value.name || user.value.id || 'U';
	return name.charAt(0).toUpperCase();
});

const loadUser = async () => {
	const stored = uni.getStorageSync('user');
	if (stored) {
		user.value = stored;
		const token = uni.getStorageSync('token');
		if (stored.id && token && !stored.name) {
			try {
				const infoResp = await getStudentInfo(stored.id, token, stored.id);
				if (infoResp?.data?.success && infoResp.data.data) {
					const fields = infoResp.data.data.split('\t\r');
					const merged = {
						...stored,
						name: fields[0] || '',
						gender: fields[1] || '',
						major: fields[2] || '',
						college: fields[3] || '',
						department: fields[4] || ''
					};
					user.value = merged;
					uni.setStorageSync('user', merged);
				}
			} catch (e) {
				// keep local data
			}
		}
	}
};

onMounted(loadUser);
onShow(loadUser);

const handleLogout = () => {
	uni.showModal({
		title: '确认退出',
		content: '确定要退出当前账号吗？',
		success: (res) => {
			if (res.confirm) logout();
		}
	});
};

const goTo = (url) => uni.navigateTo({ url });
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.user-header {
	background: linear-gradient(125deg, #1a57e8 0%, #2f86ff 45%, #18bcff 100%);
	border-radius: 30rpx;
	padding: 52rpx 34rpx;
	display: flex;
	align-items: center;
	margin-bottom: 24rpx;
	box-shadow: 0 20rpx 40rpx rgba(23, 70, 170, 0.28);
}

.avatar-box {
	width: 120rpx;
	height: 120rpx;
	border-radius: 60rpx;
	background: rgba(255, 255, 255, 0.22);
	border: 2rpx solid rgba(255, 255, 255, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
}

.avatar-text {
	font-size: 48rpx;
	font-weight: 700;
	color: #fff;
}

.user-info {
	margin-left: 24rpx;
}

.user-name {
	display: block;
	font-size: 38rpx;
	font-weight: 700;
	color: #fff;
}

.user-role {
	display: block;
	margin-top: 6rpx;
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.9);
}

.info-card,
.menu-list {
	background: rgba(255, 255, 255, 0.9);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 24rpx;
	box-shadow: 0 10rpx 24rpx rgba(26, 54, 118, 0.1);
}

.info-card {
	padding: 26rpx;
	margin-bottom: 18rpx;
}

.card-title {
	display: block;
	font-size: 29rpx;
	font-weight: 700;
	color: #1f2f53;
	margin-bottom: 12rpx;
}

.info-row {
	display: flex;
	justify-content: space-between;
	padding: 14rpx 0;
	border-bottom: 1rpx solid #eef2fb;
}

.info-row:last-child {
	border-bottom: none;
}

.info-label {
	font-size: 24rpx;
	color: #69789a;
}

.info-val {
	font-size: 24rpx;
	font-weight: 600;
	color: #2c3d63;
}

.menu-list {
	padding: 0 24rpx;
	margin-bottom: 26rpx;
}

.menu-item {
	display: flex;
	align-items: center;
	padding: 28rpx 0;
	border-bottom: 1rpx solid #edf2fb;
}

.menu-item:last-child {
	border-bottom: none;
}

.menu-icon {
	width: 36rpx;
	height: 36rpx;
	margin-right: 16rpx;
}

.menu-text {
	flex: 1;
	font-size: 27rpx;
	font-weight: 600;
	color: #223458;
}

.arrow {
	font-size: 24rpx;
	color: #7f8ba9;
}

.logout-btn {
	height: 88rpx;
	line-height: 88rpx;
	font-size: 28rpx;
	font-weight: 700;
	color: #e53935;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(229, 57, 53, 0.25);
	box-shadow: 0 10rpx 22rpx rgba(53, 75, 125, 0.08);
}
</style>
