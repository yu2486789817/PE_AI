<template>
	<PageLayout>
		<view class="container">
			<MobilePageHeader title="我的作业" subtitle="查看各课程作业进度与截止时间。" />

			<view class="loading" v-if="loading"><text class="loading-text">正在加载作业...</text></view>

			<MobileEmptyState v-else-if="assignments.length === 0" title="暂无作业" description="当前没有可查看的作业。" />

			<view v-else class="list-wrap">
				<!-- 筛选 / 排序 -->
				<view class="filter-bar">
					<picker class="filter-item" mode="selector" :range="statusOptions" range-key="label" :value="statusIndex" @change="onStatusChange">
						<view class="filter-pill">
							<text class="filter-text">{{ statusOptions[statusIndex].label }}</text>
							<text class="filter-caret">▾</text>
						</view>
					</picker>
					<picker class="filter-item" mode="selector" :range="courseOptions" range-key="label" :value="courseIndex" @change="onCourseChange">
						<view class="filter-pill">
							<text class="filter-text">{{ courseOptions[courseIndex].label }}</text>
							<text class="filter-caret">▾</text>
						</view>
					</picker>
					<picker class="filter-item" mode="selector" :range="sortOptions" range-key="label" :value="sortIndex" @change="onSortChange">
						<view class="filter-pill">
							<text class="filter-text">{{ sortOptions[sortIndex].label }}</text>
							<text class="filter-caret">▾</text>
						</view>
					</picker>
				</view>

				<MobileEmptyState v-if="visibleAssignments.length === 0" title="无匹配作业" description="换个筛选条件试试。" />

				<ListCard v-for="item in visibleAssignments" :key="item.id" @click="goToDetail(item)">
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
import { ref, computed, onMounted } from 'vue'
import { getStudentAssignments } from '@/services/studentAssignments'
import PageLayout from '@/components/PageLayout.vue'
import MobilePageHeader from '@/components/ui/MobilePageHeader.vue'
import ListCard from '@/components/ui/ListCard.vue'
import StatusChip from '@/components/ui/StatusChip.vue'
import MobileEmptyState from '@/components/ui/MobileEmptyState.vue'

const assignments = ref([])
const loading = ref(true)

// 筛选 / 排序状态
const statusIndex = ref(0)
const courseIndex = ref(0)
const sortIndex = ref(0)

const statusOptions = [
	{ label: '全部状态', value: 'all' },
	{ label: '进行中', value: '进行中' },
	{ label: '已完成', value: '已完成' },
	{ label: '已截止', value: '已截止' }
]

const sortOptions = [
	{ label: '截止时间（近→远）', value: 'deadline-asc' },
	{ label: '截止时间（远→近）', value: 'deadline-desc' }
]

// 课程下拉：基于已加载作业动态生成
const courseOptions = computed(() => {
	const seen = new Map()
	for (const hw of assignments.value) {
		if (hw.courseId && !seen.has(hw.courseId)) {
			seen.set(hw.courseId, hw.courseName || hw.courseId)
		}
	}
	return [{ label: '全部课程', value: 'all' }, ...Array.from(seen, ([value, label]) => ({ label, value }))]
})

const onStatusChange = (e) => { statusIndex.value = Number(e.detail.value) }
const onCourseChange = (e) => { courseIndex.value = Number(e.detail.value) }
const onSortChange = (e) => { sortIndex.value = Number(e.detail.value) }

const visibleAssignments = computed(() => {
	const status = statusOptions[statusIndex.value]?.value || 'all'
	const course = courseOptions.value[courseIndex.value]?.value || 'all'
	const sort = sortOptions[sortIndex.value]?.value || 'deadline-asc'

	let list = assignments.value.filter((hw) => {
		const matchStatus = status === 'all' || hw.statusText === status
		const matchCourse = course === 'all' || hw.courseId === course
		return matchStatus && matchCourse
	})

	const toTime = (s) => {
		const t = new Date(s).getTime()
		return Number.isNaN(t) ? Infinity : t
	}
	list = [...list].sort((a, b) => {
		const diff = toTime(a.deadline) - toTime(b.deadline)
		return sort === 'deadline-asc' ? diff : -diff
	})
	return list
})

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

.filter-bar {
	display: flex;
	gap: 12rpx;
	margin-bottom: 6rpx;
	flex-wrap: wrap;
}

.filter-item {
	flex: 1;
	min-width: 0;
}

.filter-pill {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 6rpx;
	padding: 12rpx 18rpx;
	background: rgba(255, 255, 255, 0.92);
	border: 2rpx solid rgba(35, 109, 242, 0.18);
	border-radius: 999rpx;
	box-shadow: 0 6rpx 16rpx rgba(24, 53, 114, 0.06);
}

.filter-text {
	font-size: 22rpx;
	font-weight: 600;
	color: var(--color-ink-700, #2c3a5e);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.filter-caret {
	font-size: 20rpx;
	color: var(--color-primary-600, #236df2);
	flex-shrink: 0;
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
