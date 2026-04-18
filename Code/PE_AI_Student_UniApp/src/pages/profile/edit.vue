<template>
	<PageLayout>
		<view class="container">
		<view class="form-box">
			<view class="input-item">
				<text class="label">姓名</text>
				<input class="input" v-model="editInfo.name" placeholder="请输入姓名" />
			</view>
			<view class="input-item">
				<text class="label">性别</text>
				<picker :range="['男', '女']" @change="onGenderChange">
					<view class="picker-box">{{ editInfo.gender }}</view>
				</picker>
			</view>
			<view class="input-item">
				<text class="label">专业</text>
				<input class="input" v-model="editInfo.major" placeholder="请输入专业" />
			</view>
			<view class="input-item">
				<text class="label">学院</text>
				<input class="input" v-model="editInfo.college" placeholder="请输入学院" />
			</view>
			<view class="input-item">
				<text class="label">系别</text>
				<input class="input" v-model="editInfo.department" placeholder="请输入系别" />
			</view>
			<button class="save-btn" :loading="saving" @click="handleSave">保存修改</button>
		</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import request from '@/services/request';
import PageLayout from '@/components/PageLayout.vue';

const saving = ref(false);
const editInfo = reactive({ name: '', gender: '男', major: '', college: '', department: '' });

const onGenderChange = (e) => {
	editInfo.gender = ['男', '女'][e.detail.value];
};

onMounted(() => {
	const user = uni.getStorageSync('user');
	if (user) {
		editInfo.name = user.name || '';
		editInfo.gender = user.gender || '男';
		editInfo.major = user.major || '';
		editInfo.college = user.college || '';
		editInfo.department = user.department || '';
	}
});

const handleSave = async () => {
	if (!editInfo.name || !editInfo.college || !editInfo.department) {
		uni.showToast({ title: '请填写必填项', icon: 'none' });
		return;
	}

	saving.value = true;
	const user = uni.getStorageSync('user');
	const token = uni.getStorageSync('token');
	try {
		const resp = await request.post('/User/change_student_info', {
			first: user?.id,
			second: token,
			third: editInfo.name,
			fourth: editInfo.gender,
			fifth: editInfo.major,
			sixth: editInfo.college,
			seventh: editInfo.department
		});

		if (!resp.data?.success) {
			uni.showToast({ title: resp.data?.message || '修改失败', icon: 'none' });
			return;
		}

		const updated = { ...user, ...editInfo };
		uni.setStorageSync('user', updated);
		uni.showToast({ title: '修改成功' });
		setTimeout(() => uni.navigateBack(), 1000);
	} catch (e) {
		uni.showToast({ title: '修改失败', icon: 'none' });
	} finally {
		saving.value = false;
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

.input,
.picker-box {
	height: 82rpx;
	line-height: 82rpx;
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
</style>
