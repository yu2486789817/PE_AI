<template>
	<PageLayout>
		<view class="container">
			<MobilePageHeader title="智慧运动课堂" subtitle="记录每一次进步，让训练反馈更科学。" />

			<InfoCard>
				<view class="action-grid">
					<view class="action-item" @click="goTo('/pages/assignments/list')">
						<text class="action-title">我的作业</text>
						<text class="action-desc">查看待完成任务</text>
					</view>
					<view class="action-item" @click="goTo('/pages/assistant/chat')">
						<text class="action-title">AI 助手</text>
						<text class="action-desc">获取训练建议</text>
					</view>
				</view>
			</InfoCard>

			<InfoCard title="个性化健康报告" class="mt-3">
				<view class="report-entry" @click="openHealthReportDialog">
					<text class="report-entry-title">基于当前情况生成长期训练建议</text>
					<text class="report-entry-arrow">›</text>
				</view>
			</InfoCard>

			<view class="section-header mt-4">
				<text class="section-title">我的课程</text>
				<button class="btn-outline" @click="showJoinDialog = true">加入课程</button>
			</view>

			<view class="loading" v-if="loadingCourses"><text class="loading-text">正在加载课程...</text></view>
			<MobileEmptyState v-else-if="courses.length === 0" title="暂无课程" description="点击“加入课程”输入邀请码开始学习。" />

			<view v-else class="list-wrap">
				<ListCard v-for="c in courses" :key="c.id" @click="goToCourse(c)">
					<view class="course-top">
						<text class="course-name">{{ c.name }}</text>
						<StatusChip :value="c.isActive" />
					</view>
					<text class="course-desc">{{ c.description || '暂无课程描述' }}</text>
					<view class="course-bottom">
						<text class="course-meta">作业：{{ c.completedAssignments }}/{{ c.totalAssignments }}</text>
						<text class="course-meta">完成率：{{ c.completionRate }}%</text>
					</view>
				</ListCard>
			</view>

			<view class="mask" v-if="showJoinDialog" @click="showJoinDialog = false">
				<view class="dialog" @click.stop>
					<text class="dialog-title">加入课程</text>
					<input class="input-base" v-model="courseCode" placeholder="请输入 6 位课程码" maxlength="6" />
					<view class="dialog-btns">
						<button class="btn-outline" @click="showJoinDialog = false">取消</button>
						<button class="btn-primary" @click="handleJoin">加入</button>
					</view>
				</view>
			</view>

			<view class="health-mask" v-if="showHealthDialog" @click="closeHealthReportDialog">
				<view class="health-dialog" @click.stop>
					<view class="health-head">
						<text class="health-title">个性化健康报告</text>
						<text class="health-close" @click="closeHealthReportDialog">×</text>
					</view>
					<input class="input-base health-field" v-model="healthHeight" type="number" placeholder="身高(cm，可选)" />
					<input class="input-base health-field" v-model="healthWeight" type="number" placeholder="体重(kg，可选)" />
					<textarea class="textarea-base health-query" v-model="healthQuery" maxlength="500" placeholder="请输入你希望咨询的问题，例如：给我一个 4 周体能提升训练计划。" />
					<button class="btn-primary health-generate" :disabled="healthLoading || !healthQuery.trim()" @click="generateHealthReport">
						<text class="btn-text">{{ healthLoading ? '生成中...' : '生成健康报告' }}</text>
					</button>
					<view class="health-error" v-if="healthError"><text>{{ healthError }}</text></view>
					<scroll-view scroll-y class="health-report" v-if="healthContent">
						<text class="health-report-text">{{ healthContent }}</text>
					</scroll-view>
					<view class="health-actions">
						<button class="btn-outline" v-if="healthContent" @click="downloadHealthReport">下载</button>
						<button class="btn-outline" @click="closeHealthReportDialog">关闭</button>
					</view>
				</view>
			</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStudentCourses, joinCourse } from '@/services/course'
import request from '@/services/request'
import PageLayout from '@/components/PageLayout.vue'
import MobilePageHeader from '@/components/ui/MobilePageHeader.vue'
import InfoCard from '@/components/ui/InfoCard.vue'
import ListCard from '@/components/ui/ListCard.vue'
import StatusChip from '@/components/ui/StatusChip.vue'
import MobileEmptyState from '@/components/ui/MobileEmptyState.vue'

const courses = ref([])
const loadingCourses = ref(false)
const showJoinDialog = ref(false)
const courseCode = ref('')
const showHealthDialog = ref(false)
const healthHeight = ref('')
const healthWeight = ref('')
const healthQuery = ref('')
const healthContent = ref('')
const healthError = ref('')
const healthLoading = ref(false)

onMounted(() => {
	fetchCourses()
})

const fetchCourseStats = async (courseId, studentId, token) => {
	try {
		const hwResp = await request.post('/Homework/get_homework_id_by_course', {
			first: '0',
			second: studentId,
			third: token,
			fourth: courseId
		})

		if (!hwResp.data?.success || !hwResp.data?.data || hwResp.data.data === 'NULL') {
			return { totalAssignments: 0, completedAssignments: 0 }
		}

		const homeworkIds = hwResp.data.data.split('\t\r').filter(Boolean)
		let completedAssignments = 0
		for (const hwId of homeworkIds) {
			const submitResp = await request.post('/Homework/get_submit_id_by_student', {
				first: '0',
				second: studentId,
				third: token,
				fourth: hwId,
				fifth: studentId
			})
			if (submitResp.data?.success && submitResp.data?.data && submitResp.data.data !== 'NULL') {
				completedAssignments += 1
			}
		}

		return {
			totalAssignments: homeworkIds.length,
			completedAssignments
		}
	} catch (e) {
		return { totalAssignments: 0, completedAssignments: 0 }
	}
}

const fetchCourses = async () => {
	loadingCourses.value = true
	const user = uni.getStorageSync('user')
	const token = uni.getStorageSync('token')
	if (!user?.id) {
		loadingCourses.value = false
		return
	}

	const res = await getStudentCourses(user.id)
	if (res.success && res.data) {
		const enriched = await Promise.all(
			res.data.map(async (c) => {
				const stats = await fetchCourseStats(c.id, user.id, token)
				return {
					...c,
					description: c.info || '',
					totalAssignments: stats.totalAssignments,
					completedAssignments: stats.completedAssignments,
					completionRate: stats.totalAssignments > 0 ? Math.round((stats.completedAssignments / stats.totalAssignments) * 100) : 0
				}
			})
		)
		courses.value = enriched
	} else {
		courses.value = []
	}
	loadingCourses.value = false
}

const handleJoin = async () => {
	const code = (courseCode.value || '').trim().toUpperCase()
	if (!/^[A-Z0-9]{6}$/.test(code)) {
		uni.showToast({ title: '请输入 6 位课程码', icon: 'none' })
		return
	}
	const user = uni.getStorageSync('user')
	const res = await joinCourse(user?.id, code)
	if (res.success) {
		uni.showToast({ title: '加入成功' })
		showJoinDialog.value = false
		courseCode.value = ''
		fetchCourses()
	} else {
		uni.showToast({ title: res.message || '加入失败', icon: 'none' })
	}
}

const openHealthReportDialog = () => {
	showHealthDialog.value = true
	healthError.value = ''
	healthContent.value = ''
	healthQuery.value = ''
}

const closeHealthReportDialog = () => {
	if (healthLoading.value) return
	showHealthDialog.value = false
}

const generateHealthReport = async () => {
	const user = uni.getStorageSync('user') || {}
	if (!user?.id || !healthQuery.value.trim()) return
	healthLoading.value = true
	healthError.value = ''
	healthContent.value = ''
	try {
		const payload = {
			student_id: user.id,
			analysis_type: 'personalized_tips',
			query: healthQuery.value.trim()
		}
		if (healthHeight.value || healthWeight.value) {
			payload.student_info = {}
			if (healthHeight.value) payload.student_info.height = healthHeight.value
			if (healthWeight.value) payload.student_info.weight = healthWeight.value
		}
		const response = await request.post('/chat/api/analysis/generate', payload)
		if (response.data?.success && response.data?.data?.report) {
			healthContent.value = response.data.data.report
			return
		}
		healthError.value = response.data?.error || '生成失败'
	} catch (err) {
		healthError.value = err?.message || '生成失败，请稍后重试'
	} finally {
		healthLoading.value = false
	}
}

const downloadHealthReport = () => {
	if (!healthContent.value) return
	const fileName = `健康报告_${new Date().toISOString().slice(0, 10)}.md`
	// #ifdef H5
	const blob = new Blob([healthContent.value], { type: 'text/markdown;charset=utf-8' })
	const url = URL.createObjectURL(blob)
	const link = document.createElement('a')
	link.href = url
	link.download = fileName
	document.body.appendChild(link)
	link.click()
	document.body.removeChild(link)
	URL.revokeObjectURL(url)
	// #endif

	// #ifndef H5
	uni.setClipboardData({
		data: healthContent.value,
		success: () => uni.showToast({ title: '报告内容已复制', icon: 'none' })
	})
	// #endif
}

const goTo = (url) => uni.switchTab({ url })
const goToCourse = (c) => uni.navigateTo({ url: `/pages/course/detail?id=${c.id}` })
</script>

<style scoped>
.container {
	padding: 28rpx;
	min-height: 100vh;
	padding-bottom: 260rpx;
}

.btn-text {
	color: inherit;
	font-size: inherit;
	font-weight: inherit;
	line-height: inherit;
}

.action-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 16rpx;
}

.action-item {
	border: 2rpx solid #d8e0ee;
	border-radius: 22rpx;
	padding: 24rpx;
	background: linear-gradient(135deg, #f2f7ff 0%, #ffffff 100%);
	box-shadow: 0 8rpx 18rpx rgba(35, 109, 242, 0.08);
}

.action-item:nth-child(2) {
	background: linear-gradient(135deg, #f0fbf7 0%, #ffffff 100%);
}

.action-title {
	display: block;
	font-size: 28rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.action-desc {
	display: block;
	margin-top: 8rpx;
	font-size: 22rpx;
	color: var(--color-ink-500);
}

.report-entry {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.report-entry-title {
	font-size: 25rpx;
	color: var(--color-ink-700);
}

.report-entry-arrow {
	font-size: 28rpx;
	color: var(--color-ink-500);
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 14rpx;
}

.section-title {
	font-size: 31rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.list-wrap {
	display: flex;
	flex-direction: column;
	gap: 14rpx;
}

.course-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 10rpx;
}

.course-name {
	font-size: 30rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.course-desc {
	display: block;
	font-size: 24rpx;
	line-height: 1.6;
	color: var(--color-ink-500);
	margin-bottom: 12rpx;
}

.course-bottom {
	display: flex;
	gap: 20rpx;
}

.course-meta {
	font-size: 22rpx;
	color: var(--color-ink-600);
}

.loading {
	padding: 72rpx 20rpx;
	text-align: center;
}

.loading-text {
	font-size: 24rpx;
	color: var(--color-ink-500);
}

.mask,
.health-mask {
	position: fixed;
	inset: 0;
	background: rgba(10, 20, 44, 0.45);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
	padding: 24rpx;
}

.dialog,
.health-dialog {
	width: 100%;
	background: #fff;
	border-radius: var(--radius-xl);
	padding: 28rpx;
}

.health-generate {
	width: 100%;
	color: #ffffff;
	margin-top: 22rpx;
}

.health-generate[disabled] {
	color: #ffffff;
	background: linear-gradient(120deg, #b9cdf2 0%, #c5e0f5 100%);
	box-shadow: 0 10rpx 22rpx rgba(35, 109, 242, 0.14);
	opacity: 1;
}

.dialog-title {
	display: block;
	text-align: center;
	font-size: 32rpx;
	font-weight: 700;
	color: var(--color-ink-900);
	margin-bottom: 20rpx;
}

.dialog-btns {
	display: flex;
	gap: 12rpx;
	margin-top: 16rpx;
}

.dialog-btns button {
	flex: 1;
}

.health-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 22rpx;
}

.health-title {
	font-size: 30rpx;
	font-weight: 700;
	color: var(--color-ink-900);
}

.health-close {
	font-size: 44rpx;
	line-height: 1;
	color: var(--color-ink-500);
}

.health-field,
.health-query {
	width: 100%;
	margin-top: 18rpx;
	background: #f8fbff;
	border: 2rpx solid #d5dfef;
	border-radius: 18rpx;
	color: #172033;
	box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.9);
}

.health-field {
	height: 86rpx;
	line-height: 86rpx;
	padding: 0 22rpx;
}

.health-query {
	min-height: 152rpx;
	padding: 18rpx 22rpx;
	line-height: 1.55;
}

.health-error {
	margin-top: 10rpx;
	padding: 12rpx;
	border-radius: 10rpx;
	background: #ffe9ea;
	color: #bf3d3d;
	font-size: 22rpx;
}

.health-report {
	margin-top: 12rpx;
	max-height: 320rpx;
	padding: 14rpx;
	border-radius: 12rpx;
	background: #f8faff;
	border: 1rpx solid #e2e9fc;
}

.health-report-text {
	font-size: 23rpx;
	line-height: 1.7;
	color: var(--color-ink-600);
	white-space: pre-wrap;
}

.health-actions {
	display: flex;
	gap: 12rpx;
	margin-top: 22rpx;
}

.health-actions button {
	flex: 1;
}
</style>
