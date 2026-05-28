<template>
	<view class="register-container">
		<view class="logo-box">
			<text class="app-name">PE AI 智慧体育</text>
			<text class="sub-title">学生注册</text>
		</view>

		<view class="form-box">
			<view class="input-item">
				<text class="label">学号</text>
				<input class="input" v-model="formData.id" placeholder="请输入学号" />
			</view>
			<view class="input-item">
				<text class="label">密码</text>
				<input class="input" v-model="formData.password" password placeholder="请输入密码" />
			</view>
			<view class="input-item">
				<text class="label">确认密码</text>
				<input class="input" v-model="confirmPassword" password placeholder="请再次输入密码" />
			</view>
			<view class="input-item">
				<text class="label">姓名</text>
				<input class="input" v-model="formData.name" placeholder="请输入姓名" />
			</view>
			<view class="input-item">
				<text class="label">性别</text>
				<picker :range="['男', '女']" @change="onGenderChange">
					<view class="picker-box">{{ formData.gender || '请选择' }}</view>
				</picker>
			</view>
			<view class="input-item">
				<text class="label">专业</text>
				<input class="input" v-model="formData.major" placeholder="请输入专业" />
			</view>
			<view class="input-item">
				<text class="label">学院</text>
				<input class="input" v-model="formData.college" placeholder="请输入学院" />
			</view>
			<view class="input-item">
				<text class="label">系别</text>
				<input class="input" v-model="formData.department" placeholder="请输入系别" />
			</view>

			<text class="error-msg" v-if="errorMsg">{{ errorMsg }}</text>

			<button class="register-btn" :disabled="loading" @click="handleRegister">
				<text class="register-btn-text">{{ loading ? '注册中...' : '注册' }}</text>
			</button>

			<view class="footer-links">
				<text class="link" @click="goToLogin">已有账号？去登录</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, reactive } from 'vue';
import request from '@/services/request';
import CryptoJS from 'crypto-js';

const confirmPassword = ref('');
const loading = ref(false);
const errorMsg = ref('');

const formData = reactive({
	id: '',
	password: '',
	name: '',
	gender: '男',
	major: '',
	college: '',
	department: ''
});

const onGenderChange = (e) => {
	formData.gender = ['男', '女'][e.detail.value];
};

const handleRegister = async () => {
	if (!formData.id || !formData.password || !formData.name || !formData.major || !formData.college || !formData.department) {
		errorMsg.value = '请填写所有字段';
		return;
	}
	if (formData.password !== confirmPassword.value) {
		errorMsg.value = '两次密码不一致';
		return;
	}

	loading.value = true;
	errorMsg.value = '';
	try {
		const hash = CryptoJS.SHA256(formData.password).toString();
		const resp = await request.post('/User/new_student', {
			first: formData.id,
			second: hash,
			third: formData.name,
			fourth: formData.gender,
			fifth: formData.major,
			sixth: formData.college,
			seventh: formData.department
		});

		if (resp.data?.success) {
			uni.showToast({ title: '注册成功' });
			setTimeout(() => uni.navigateBack(), 1000);
		} else {
			errorMsg.value = resp.data?.message || '注册失败，请检查信息';
		}
	} catch (err) {
		errorMsg.value = '注册失败，请检查信息';
	} finally {
		loading.value = false;
	}
};

const goToLogin = () => uni.navigateBack();
</script>

<style scoped>
.register-container {
	min-height: 100vh;
	padding: 44rpx;
	background:
		radial-gradient(circle at 14% 12%, rgba(29, 99, 255, 0.16), transparent 34%),
		radial-gradient(circle at 88% 10%, rgba(24, 183, 255, 0.18), transparent 32%),
		linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
}

.logo-box {
	text-align: center;
	margin-bottom: 30rpx;
	padding-top: 18rpx;
}

.app-name {
	display: block;
	font-size: 40rpx;
	font-weight: 700;
	letter-spacing: 1rpx;
	color: #17305c;
}

.sub-title {
	display: block;
	font-size: 24rpx;
	margin-top: 10rpx;
	color: #63739a;
}

.form-box {
	background: rgba(255, 255, 255, 0.86);
	border: 2rpx solid rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(14rpx);
	border-radius: 30rpx;
	padding: 34rpx;
	box-shadow: 0 16rpx 40rpx rgba(28, 69, 150, 0.12);
}

.input-item {
	margin-bottom: 20rpx;
}

.label {
	display: block;
	font-size: 23rpx;
	font-weight: 600;
	color: #607094;
	margin-bottom: 10rpx;
}

.input,
.picker-box {
	height: 82rpx;
	line-height: 82rpx;
	padding: 0 22rpx;
	border-radius: 16rpx;
	background: #f3f7ff;
	border: 2rpx solid #dfe8ff;
	font-size: 28rpx;
	color: #1b2740;
}

.error-msg {
	display: block;
	padding: 12rpx 18rpx;
	border-radius: 12rpx;
	background: rgba(239, 68, 68, 0.1);
	color: #ce2f2f;
	font-size: 22rpx;
	margin-bottom: 10rpx;
}

.register-btn {
	margin-top: 26rpx;
	height: 90rpx;
	line-height: 90rpx;
	font-size: 30rpx;
	font-weight: 700;
	color: #fff;
	border-radius: 999rpx;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	box-shadow: 0 12rpx 24rpx rgba(29, 99, 255, 0.33);
}

.register-btn[disabled] {
	background: linear-gradient(120deg, #9fbff8 0%, #a8d6fb 100%);
	opacity: 1;
}

.register-btn-text {
	color: #fff;
	font-size: 30rpx;
	font-weight: 700;
	line-height: 90rpx;
}

.footer-links {
	margin-top: 24rpx;
	text-align: center;
}

.link {
	font-size: 24rpx;
	font-weight: 600;
	color: #2a61d9;
}
</style>
