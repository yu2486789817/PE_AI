<template>
	<view class="login-container">
		<view class="logo-box">
			<image class="logo" src="/static/images/logo.png" mode="aspectFit"></image>
			<text class="app-name">PE AI 智慧体育</text>
		</view>

		<view class="form-box">
			<view class="input-item">
				<text class="label">学号</text>
				<input class="input" v-model="studentId" placeholder="请输入你的学号" />
			</view>
			<view class="input-item">
				<text class="label">密码</text>
				<input class="input" v-model="password" password placeholder="请输入登录密码" />
			</view>

			<button class="login-btn" :loading="loading" @click="handleLogin">学生登录</button>

			<view class="footer-links">
				<text class="link" @click="goToRegister">还没有账号？去注册</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue';
import { loginStudent } from '@/services/auth';

const studentId = ref('');
const password = ref('');
const loading = ref(false);

const handleLogin = async () => {
	if (!studentId.value || !password.value) {
		uni.showToast({ title: '请输入学号和密码', icon: 'none' });
		return;
	}

	loading.value = true;
	const res = await loginStudent(studentId.value, password.value);
	loading.value = false;

	if (res.success) {
		uni.showToast({ title: '登录成功' });
		setTimeout(() => {
			uni.switchTab({ url: '/pages/index/index' });
		}, 800);
	} else {
		uni.showToast({ title: res.message || '登录失败', icon: 'none' });
	}
};

const goToRegister = () => {
	uni.navigateTo({ url: '/pages/login/register' });
};
</script>

<style scoped>
.login-container {
	min-height: 100vh;
	padding: 64rpx 44rpx;
	display: flex;
	flex-direction: column;
	justify-content: center;
	background:
		radial-gradient(circle at 10% 10%, rgba(29, 99, 255, 0.16), transparent 34%),
		radial-gradient(circle at 90% 20%, rgba(24, 183, 255, 0.18), transparent 30%),
		linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
}

.logo-box {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 56rpx;
}

.logo {
	width: 168rpx;
	height: 168rpx;
	filter: drop-shadow(0 12rpx 22rpx rgba(35, 79, 168, 0.2));
}

.app-name {
	font-size: 46rpx;
	font-weight: 700;
	letter-spacing: 1rpx;
	margin-top: 18rpx;
	color: #17305c;
}

.form-box {
	background: rgba(255, 255, 255, 0.82);
	border: 2rpx solid rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(14rpx);
	border-radius: 30rpx;
	padding: 40rpx 34rpx 34rpx;
	box-shadow: 0 16rpx 42rpx rgba(27, 66, 145, 0.12);
	animation: rise 0.45s ease;
}

.input-item {
	margin-bottom: 24rpx;
}

.label {
	display: block;
	font-size: 24rpx;
	font-weight: 600;
	color: #5c6d90;
	margin-bottom: 10rpx;
}

.input {
	height: 90rpx;
	padding: 0 24rpx;
	border-radius: 18rpx;
	background: #f3f7ff;
	border: 2rpx solid #dfe8ff;
	font-size: 30rpx;
	color: #172033;
}

.login-btn {
	margin-top: 30rpx;
	height: 92rpx;
	line-height: 92rpx;
	font-size: 30rpx;
	font-weight: 700;
	color: #fff;
	border-radius: 999rpx;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	box-shadow: 0 12rpx 24rpx rgba(29, 99, 255, 0.35);
}

.footer-links {
	margin-top: 28rpx;
	text-align: center;
}

.link {
	font-size: 24rpx;
	font-weight: 600;
	color: #2a61d9;
}

@keyframes rise {
	from {
		opacity: 0;
		transform: translateY(20rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
