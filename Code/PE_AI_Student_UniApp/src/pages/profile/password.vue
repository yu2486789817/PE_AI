<template>
	<PageLayout>
		<view class="container">
		<view class="form-box">
			<view class="input-item">
				<text class="label">旧密码</text>
				<input class="input" v-model="oldPwd" password placeholder="请输入旧密码" />
			</view>
			<view class="input-item">
				<text class="label">新密码</text>
				<input class="input" v-model="newPwd" password placeholder="请输入新密码" />
			</view>
			<view class="input-item">
				<text class="label">确认新密码</text>
				<input class="input" v-model="confirmPwd" password placeholder="请再次输入新密码" />
			</view>
			<button class="save-btn" :disabled="saving" @click="handleChange">
				<text class="save-btn-text">{{ saving ? '修改中...' : '确认修改' }}</text>
			</button>
		</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref } from 'vue';
import { changePassword } from '@/services/auth';
import PageLayout from '@/components/PageLayout.vue';

const oldPwd = ref('');
const newPwd = ref('');
const confirmPwd = ref('');
const saving = ref(false);

const handleChange = async () => {
	if (!oldPwd.value || !newPwd.value) {
		uni.showToast({ title: '请填写密码', icon: 'none' });
		return;
	}
	if (newPwd.value !== confirmPwd.value) {
		uni.showToast({ title: '两次密码不一致', icon: 'none' });
		return;
	}
	if (newPwd.value.length < 6) {
		uni.showToast({ title: '密码至少 6 位', icon: 'none' });
		return;
	}

	saving.value = true;
	const user = uni.getStorageSync('user');
	const res = await changePassword(user?.id, oldPwd.value, newPwd.value);
	saving.value = false;

	if (res.success) {
		uni.showToast({ title: '修改成功' });
		setTimeout(() => uni.navigateBack(), 1200);
	} else {
		uni.showToast({ title: res.message || '修改失败', icon: 'none' });
	}
};
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.form-box {
	background: rgba(255, 255, 255, 0.9);
	border: 2rpx solid rgba(255, 255, 255, 0.88);
	border-radius: 26rpx;
	padding: 28rpx;
	box-shadow: 0 12rpx 28rpx rgba(24, 52, 113, 0.1);
}

.input-item {
	margin-bottom: 20rpx;
}

.label {
	display: block;
	font-size: 23rpx;
	font-weight: 600;
	color: #5e6e92;
	margin-bottom: 10rpx;
}

.input {
	height: 82rpx;
	padding: 0 22rpx;
	border-radius: 16rpx;
	background: #f3f7ff;
	border: 2rpx solid #dfe8ff;
	font-size: 28rpx;
	color: #1c2c4f;
}

.save-btn {
	margin-top: 24rpx;
	height: 88rpx;
	line-height: 88rpx;
	font-size: 29rpx;
	font-weight: 700;
	color: #fff;
	border-radius: 999rpx;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	box-shadow: 0 12rpx 24rpx rgba(29, 99, 255, 0.32);
}

.save-btn[disabled] {
	background: linear-gradient(120deg, #9fbff8 0%, #a8d6fb 100%);
	opacity: 1;
}

.save-btn-text {
	color: #fff;
	font-size: 29rpx;
	font-weight: 700;
	line-height: 88rpx;
}
</style>
