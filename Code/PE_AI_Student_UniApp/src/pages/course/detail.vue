<template>
	<PageLayout>
		<view class="container">
			<MobilePageHeader title="课程详情" subtitle="查看课程信息、作业和教学视频。" />

			<view class="loading" v-if="loading"><text class="loading-text">正在加载课程...</text></view>

			<InfoCard v-if="course" :title="course.name">
				<text class="course-desc">{{ course.description || '暂无课程描述' }}</text>
				<view class="info-row"><text class="info-label">课程号</text><text class="info-val">{{ course.subject || '-' }}</text></view>
				<view class="info-row"><text class="info-label">授课教师</text><text class="info-val">{{ course.teacherName }}</text></view>
				<view class="info-row"><text class="info-label">状态</text><StatusChip :value="course.statusText" /></view>
			</InfoCard>

			<InfoCard v-if="course" class="mt-3">
				<view class="video-entry" @click="goToVideos">
					<text class="video-title">教学视频</text>
					<text class="video-arrow">></text>
				</view>
			</InfoCard>

			<view class="section-header" v-if="course"><text class="section-title">课程作业</text></view>

			<view v-if="assignments.length > 0" class="list-wrap">
				<ListCard v-for="item in assignments" :key="item.id" @click="goToAssignment(item)">
					<view class="assignment-top">
						<text class="assignment-title">{{ item.title }}</text>
						<StatusChip :value="item.statusText" />
					</view>
					<text class="assignment-desc">{{ item.description || '暂无描述' }}</text>
					<text class="assignment-deadline">截止时间：{{ formatDate(item.deadline) }}</text>
				</ListCard>
			</view>

			<MobileEmptyState v-else-if="course" title="暂无作业" description="当前课程尚未发布作业。" />
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/services/request'
import PageLayout from '@/components/PageLayout.vue'
import MobilePageHeader from '@/components/ui/MobilePageHeader.vue'
import InfoCard from '@/components/ui/InfoCard.vue'
import ListCard from '@/components/ui/ListCard.vue'
import StatusChip from '@/components/ui/StatusChip.vue'
import MobileEmptyState from '@/components/ui/MobileEmptyState.vue'

const course = ref(null)
const assignments = ref([])
const loading = ref(true)
const courseId = ref('')

onMounted(() => {
	const pages = getCurrentPages()
	const page = pages[pages.length - 1]
	courseId.value = page.options?.id || ''
	loadCourseDetails()
})

const loadCourseDetails = async () => {
	loading.value = true
	const user = uni.getStorageSync('user')
	const token = uni.getStorageSync('token')
	try {
		const courseResp = await request.post('/Course/get_info_by_course_id', { first: courseId.value })
		if (courseResp.data?.success && courseResp.data.data) {
			const d = String(courseResp.data.data).split('\t\r')
			const teacherId = d[0] || ''
			let teacherName = '未知教师'
			try {
				const tResp = await request.post('/User/get_teacher_info', {
					first: user?.id,
					second: token,
					third: '0',
					fourth: teacherId
				})
				if (tResp.data?.success && tResp.data.data) {
					teacherName = String(tResp.data.data).split('\t\r')[0] || '未知教师'
				}
			} catch (e) {
				// ignore teacher info failure
			}

			const status = d[5] === '2' ? '已归档' : d[5] === '1' ? '进行中' : '未发布'
			course.value = {
				id: courseId.value,
				name: d[1] || '未命名课程',
				description: d[2] || '',
				subject: d[3] || '',
				statusText: status,
				teacherName
			}
		}

		const hwResp = await request.post('/Homework/get_homework_id_by_course', {
			first: '0',
			second: user?.id,
			third: token,
			fourth: courseId.value
		})

		if (hwResp.data?.success && hwResp.data.data && hwResp.data.data !== 'NULL') {
			const ids = String(hwResp.data.data).split('\t\r').filter((i) => i.trim())
			const items = []
			for (const hwId of ids) {
				try {
					const infoResp = await request.post('/Homework/get_info_by_homework_id', {
						first: courseId.value,
						second: hwId.trim()
					})
					if (infoResp.data?.success && infoResp.data.data) {
						const ad = String(infoResp.data.data).split('\t\r')
						const active = ad[2] && new Date(ad[2]) > new Date()
						items.push({
							id: hwId.trim(),
							title: ad[0] || `作业 ${hwId}`,
							description: ad[1] || '',
							deadline: ad[2] || '',
							statusText: active ? '进行中' : '已截止'
						})
					}
				} catch (e) {
					// ignore one homework failure
				}
			}
			assignments.value = items
		} else {
			assignments.value = []
		}
	} catch (err) {
		uni.showToast({ title: '加载失败', icon: 'none' })
	} finally {
		loading.value = false
	}
}

const formatDate = (s) => {
	if (!s) return '待定'
	const d = new Date(s)
	if (Number.isNaN(d.getTime())) return s
	return `${d.getMonth() + 1}月${d.getDate()}日`
}

const goToAssignment = (item) => {
	uni.navigateTo({ url: `/pages/assignments/detail?id=${item.id}&courseId=${courseId.value}` })
}

const goToVideos = () => {
	uni.navigateTo({ url: `/pages/course/videos?courseId=${courseId.value}` })
}
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
}

.loading {
	padding: 100rpx 20rpx;
	text-align: center;
}

.loading-text {
	font-size: 24rpx;
	color: var(--color-ink-500);
}

.course-desc {
	display: block;
	font-size: 24rpx;
	line-height: 1.65;
	color: var(--color-ink-500);
	margin-bottom: 16rpx;
}

.info-row {
	display: flex;
	align-items: center;
	margin-bottom: 10rpx;
}

.info-label {
	width: 100rpx;
	font-size: 22rpx;
	color: var(--color-ink-500);
}

.info-val {
	font-size: 23rpx;
	font-weight: 600;
	color: var(--color-ink-700);
}

.video-entry {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.video-title {
	font-size: 28rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.video-arrow {
	font-size: 30rpx;
	color: var(--color-ink-500);
}

.section-header {
	padding: 18rpx 2rpx 14rpx;
}

.section-title {
	font-size: 30rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.list-wrap {
	display: flex;
	flex-direction: column;
	gap: 14rpx;
}

.assignment-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10rpx;
}

.assignment-title {
	font-size: 28rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.assignment-desc {
	display: block;
	font-size: 23rpx;
	line-height: 1.6;
	color: var(--color-ink-500);
	margin-bottom: 10rpx;
}

.assignment-deadline {
	font-size: 21rpx;
	font-weight: 600;
	color: var(--color-ink-600);
}
</style>
