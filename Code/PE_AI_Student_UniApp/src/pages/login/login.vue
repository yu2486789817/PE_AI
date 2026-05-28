<template>
	<view class="login-container">
		<view class="logo-box">
			<text class="app-icon">&#127947;</text>
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

			<button class="btn-primary login-btn" :disabled="loading" @click="handleLogin">
				<text class="login-btn-text">{{ loading ? '登录中...' : '学生登录' }}</text>
			</button>

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

.app-icon {
	font-size: 120rpx;
	line-height: 1;
	text-align: center;
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
	display: flex;
	align-items: center;
	justify-content: center;
	color: #ffffff;
	background: linear-gradient(120deg, #236df2 0%, #2f94f5 100%);
}

.login-btn[disabled] {
	opacity: 0.72;
	color: #ffffff;
	background: linear-gradient(120deg, #236df2 0%, #2f94f5 100%);
}

.login-btn-text {
	color: #ffffff;
	font-size: 26rpx;
	font-weight: 700;
	line-height: 80rpx;
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
