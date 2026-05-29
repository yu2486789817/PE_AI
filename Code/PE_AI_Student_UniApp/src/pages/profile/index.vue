<template>
	<PageLayout>
		<view class="container">
			<MobilePageHeader title="个人中心" subtitle="查看与维护账号信息。" />

			<InfoCard>
				<view class="user-header">
					<view class="avatar-box"><text class="avatar-text">{{ userInitial }}</text></view>
					<view class="user-info">
						<text class="user-name">{{ user.name || '未登录' }}</text>
						<text class="user-role">学生 · {{ user.id || '-' }}</text>
					</view>
				</view>
			</InfoCard>

			<InfoCard title="账号详情" class="mt-3">
				<view class="info-row"><text class="info-label">学号</text><text class="info-val">{{ user.id || '-' }}</text></view>
				<view class="info-row"><text class="info-label">姓名</text><text class="info-val">{{ user.name || '-' }}</text></view>
				<view class="info-row"><text class="info-label">性别</text><text class="info-val">{{ user.gender || '-' }}</text></view>
				<view class="info-row"><text class="info-label">专业</text><text class="info-val">{{ user.major || '-' }}</text></view>
				<view class="info-row"><text class="info-label">学院</text><text class="info-val">{{ user.college || '-' }}</text></view>
				<view class="info-row"><text class="info-label">系别</text><text class="info-val">{{ user.department || '-' }}</text></view>
			</InfoCard>

			<InfoCard class="mt-3">
				<view class="menu-item" @click="goTo('/pages/profile/password')">
					<text class="menu-text">修改密码</text>
					<text class="arrow">›</text>
				</view>
			</InfoCard>

			<button class="btn-outline logout-btn" @click="handleLogout">退出登录</button>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { logout, getStudentInfo, buildStudentUser } from '@/services/auth'
import PageLayout from '@/components/PageLayout.vue'
import MobilePageHeader from '@/components/ui/MobilePageHeader.vue'
import InfoCard from '@/components/ui/InfoCard.vue'

const user = ref({})

const userInitial = computed(() => {
	const name = user.value.name || user.value.id || 'U'
	return name.charAt(0).toUpperCase()
})

const loadUser = async () => {
	const stored = uni.getStorageSync('user')
	if (stored) {
		user.value = stored
		const token = uni.getStorageSync('token')
		if (stored.id && token && !stored.name) {
			try {
				const infoResp = await getStudentInfo(stored.id, token, stored.id)
				if (infoResp?.data?.success && infoResp.data.data) {
					const fields = String(infoResp.data.data).split('\t\r')
					const merged = {
						...stored,
						name: fields[0] || '',
						gender: fields[1] || '',
						major: fields[2] || '',
						college: fields[3] || '',
						department: fields[4] || ''
					}
					user.value = merged
					uni.setStorageSync('user', merged)
				}
			} catch (e) {
				// keep local data
			}
		}
		return
	}

	const token = uni.getStorageSync('token')
	const studentId = uni.getStorageSync('lastStudentId')
	if (token && studentId) {
		user.value = { id: studentId, role: 'student' }
		try {
			const infoResp = await getStudentInfo(studentId, token, studentId)
			if (infoResp?.data?.success && infoResp.data.data) {
				const merged = buildStudentUser(studentId, infoResp.data.data)
				user.value = merged
				uni.setStorageSync('user', merged)
			}
		} catch (e) {
			// keep local fallback
		}
	}
}

onMounted(loadUser)
onShow(loadUser)

const handleLogout = () => {
	uni.showModal({
		title: '确认退出',
		content: '确定要退出当前账号吗？',
		success: (res) => {
			if (res.confirm) logout()
		}
	})
}

const goTo = (url) => uni.navigateTo({ url })
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.user-header {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.avatar-box {
	width: 112rpx;
	height: 112rpx;
	border-radius: 56rpx;
	background: rgba(35, 109, 242, 0.12);
	display: flex;
	align-items: center;
	justify-content: center;
}

.avatar-text {
	font-size: 42rpx;
	font-weight: 700;
	color: var(--color-primary-600);
}

.user-name {
	display: block;
	font-size: 34rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.user-role {
	display: block;
	margin-top: 6rpx;
	font-size: 23rpx;
	color: var(--color-ink-500);
}

.info-row {
	display: flex;
	justify-content: space-between;
	padding: 14rpx 0;
	border-bottom: 1rpx solid var(--color-line-100);
}

.info-row:last-child {
	border-bottom: none;
}

.info-label {
	font-size: 24rpx;
	color: var(--color-ink-500);
}

.info-val {
	font-size: 24rpx;
	font-weight: 600;
	color: var(--color-ink-700);
}

.menu-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 20rpx 0;
	border-bottom: 1rpx solid var(--color-line-100);
}

.menu-item:last-child {
	border-bottom: none;
}

.menu-text {
	font-size: 27rpx;
	font-weight: 600;
	color: var(--color-ink-700);
}

.arrow {
	font-size: 24rpx;
	color: var(--color-ink-500);
}

.logout-btn {
	width: 100%;
	margin-top: 24rpx;
	color: var(--color-danger-600);
	border-color: rgba(214, 62, 53, 0.3);
}
</style>
