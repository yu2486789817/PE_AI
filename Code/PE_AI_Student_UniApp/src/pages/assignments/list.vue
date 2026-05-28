<template>
	<PageLayout>
		<view class="container">
			<MobilePageHeader title="我的作业" subtitle="查看各课程作业进度与截止时间。" />

			<view class="loading" v-if="loading"><text class="loading-text">正在加载作业...</text></view>

			<MobileEmptyState v-else-if="assignments.length === 0" title="暂无作业" description="当前没有可查看的作业。" />

			<view v-else class="list-wrap">
				<ListCard v-for="item in assignments" :key="item.id" @click="goToDetail(item)">
					<view class="card-top">
						<text class="card-title">{{ item.title }}</text>
						<StatusChip :value="item.statusText" />
					</view>
					<text class="card-course">{{ item.courseName }}</text>
					<text class="card-desc">{{ item.description || '暂无作业说明' }}</text>
					<text class="card-deadline">截止时间：{{ formatDate(item.deadline) }}</text>
				</ListCard>
			</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStudentAssignments } from '@/services/studentAssignments'
import PageLayout from '@/components/PageLayout.vue'
import MobilePageHeader from '@/components/ui/MobilePageHeader.vue'
import ListCard from '@/components/ui/ListCard.vue'
import StatusChip from '@/components/ui/StatusChip.vue'
import MobileEmptyState from '@/components/ui/MobileEmptyState.vue'

const assignments = ref([])
const loading = ref(true)

onMounted(() => {
	loadAssignments()
})

const loadAssignments = async () => {
	loading.value = true
	const user = uni.getStorageSync('user')
	if (!user?.id) {
		loading.value = false
		return
	}

	const res = await getStudentAssignments(user.id)
	if (res.success && res.data) {
		assignments.value = res.data.map((hw) => {
			const isActive = hw.deadline && new Date(hw.deadline) > new Date()
			return {
				...hw,
				courseName: hw.courseName || hw.courseId || '',
				statusText: hw.statusText || (isActive ? '进行中' : '已截止')
			}
		})
	}
	loading.value = false
}

const formatDate = (s) => {
	if (!s) return '待定'
	const d = new Date(s)
	if (Number.isNaN(d.getTime())) return s
	return `${d.getMonth() + 1}月${d.getDate()}日`
}

const goToDetail = (item) => {
	uni.navigateTo({ url: `/pages/assignments/detail?id=${item.id}&courseId=${item.courseId}` })
}
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.loading {
	padding: 90rpx 20rpx;
	text-align: center;
}

.loading-text {
	font-size: 24rpx;
	color: var(--color-ink-500);
}

.list-wrap {
	display: flex;
	flex-direction: column;
	gap: 14rpx;
}

.card-top {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 16rpx;
	margin-bottom: 8rpx;
}

.card-title {
	font-size: 29rpx;
	font-weight: 700;
	line-height: 1.4;
	color: var(--color-ink-900);
}

.card-course {
	display: inline-block;
	padding: 6rpx 12rpx;
	margin-bottom: 10rpx;
	font-size: 22rpx;
	color: var(--color-primary-600);
	background: rgba(35, 109, 242, 0.1);
	border-radius: 999rpx;
}

.card-desc {
	display: block;
	font-size: 24rpx;
	line-height: 1.6;
	color: var(--color-ink-500);
	margin-bottom: 10rpx;
}

.card-deadline {
	font-size: 22rpx;
	font-weight: 600;
	color: var(--color-ink-600);
}
</style>
