<template>
	<view class="login-container">
		<view class="logo-box">
			<image class="logo" src="/static/images/logo.png" mode="aspectFit"></image>
			<text class="app-name">智慧体育学生端</text>
			<text class="app-sub">智能训练 · 过程可视 · 数据反馈</text>
		</view>

		<view class="form-box">
			<FormBlock label="学号">
				<input class="input-base" v-model="studentId" placeholder="请输入学号" />
			</FormBlock>
			<FormBlock label="密码">
				<input class="input-base" v-model="password" password placeholder="请输入登录密码" />
			</FormBlock>

			<button class="btn-primary login-btn" :loading="loading" @click="handleLogin">学生登录</button>

			<view class="footer-links">
				<text class="link" @click="goToRegister">还没有账号？去注册</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { loginStudent } from '@/services/auth'
import FormBlock from '@/components/ui/FormBlock.vue'

const studentId = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
	if (!studentId.value || !password.value) {
		uni.showToast({ title: '请输入学号和密码', icon: 'none' })
		return
	}

	loading.value = true
	const res = await loginStudent(studentId.value, password.value)
	loading.value = false

	if (res.success) {
		uni.showToast({ title: '登录成功' })
		setTimeout(() => {
			uni.switchTab({ url: '/pages/index/index' })
		}, 700)
	} else {
		uni.showToast({ title: res.message || '登录失败', icon: 'none' })
	}
}

const goToRegister = () => {
	uni.navigateTo({ url: '/pages/login/register' })
}
</script>

<style scoped>
.login-container {
	min-height: 100vh;
	padding: 72rpx 44rpx;
	display: flex;
	flex-direction: column;
	justify-content: center;
}

.logo-box {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 48rpx;
}

.logo {
	width: 170rpx;
	height: 170rpx;
	filter: drop-shadow(0 12rpx 22rpx rgba(35, 79, 168, 0.22));
}

.app-name {
	font-size: 44rpx;
	font-weight: 700;
	margin-top: 16rpx;
	color: var(--color-ink-900);
}

.app-sub {
	font-size: 24rpx;
	margin-top: 8rpx;
	color: var(--color-ink-500);
}

.form-box {
	background: rgba(255, 255, 255, 0.9);
	border: 2rpx solid var(--color-line-200);
	border-radius: var(--radius-xl);
	padding: 36rpx 30rpx;
	box-shadow: var(--shadow-soft);
}

.login-btn {
	width: 100%;
	margin-top: 16rpx;
}

.footer-links {
	margin-top: 24rpx;
	text-align: center;
}

.link {
	font-size: 24rpx;
	font-weight: 600;
	color: var(--color-primary-600);
}
</style>
