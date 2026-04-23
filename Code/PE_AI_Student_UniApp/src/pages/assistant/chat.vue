<template>
	<PageLayout>
		<view class="chat-container">
			<view class="chat-header glass-panel">
				<view class="header-action" @click="toggleHistory">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
						<polyline points="1 4 1 10 7 10"></polyline>
						<path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
					</svg>
				</view>

				<view class="header-center">
					<picker :range="modelNames" @change="handleModelChange">
						<view class="model-selector">
							<text class="model-name">{{ selectedModel }}</text>
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="chevron-icon">
								<polyline points="6 9 12 15 18 9"></polyline>
							</svg>
						</view>
					</picker>
				</view>

				<view class="header-action" @click="startNewChat">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
						<line x1="12" y1="5" x2="12" y2="19"></line>
						<line x1="5" y1="12" x2="19" y2="12"></line>
					</svg>
				</view>
			</view>

			<view class="action-strip">
				<button class="strip-btn" :disabled="reportLoading" @click="handleGenerateWeeklyReport">
					{{ reportLoading ? '生成中...' : '智能周报' }}
				</button>
				<button class="strip-btn" :disabled="exporting || !currentSessionId" @click="handleExportSession">
					{{ exporting ? '导出中...' : '导出MD' }}
				</button>
			</view>

			<scroll-view class="message-list" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true">
				<view class="message-wrapper" v-for="(msg, index) in messages" :key="index" :class="msg.role">
					<view class="avatar">
						<view v-if="msg.role === 'user'" class="icon-inner">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 60%; height: 60%; color: var(--brand-500);">
								<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
								<circle cx="12" cy="7" r="4"></circle>
							</svg>
						</view>
						<view v-else class="icon-inner">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 60%; height: 60%; color: var(--warning-500);">
								<rect x="3" y="11" width="18" height="10" rx="2"></rect>
								<circle cx="12" cy="5" r="2"></circle>
								<path d="M12 7v4"></path>
								<line x1="8" y1="16" x2="8" y2="16"></line>
								<line x1="16" y1="16" x2="16" y2="16"></line>
							</svg>
						</view>
					</view>
					<view class="content-box"><text class="content">{{ msg.content }}</text></view>
				</view>
				<view class="padding-bottom"></view>
			</scroll-view>

			<view class="input-area">
				<textarea class="message-input" v-model="inputText" auto-height placeholder="向 AI 助手提问训练问题..." />
				<button class="send-btn" :disabled="!inputText.trim() || sending" @click="handleSend">
					<text v-if="!sending">发送</text>
					<text v-else>...</text>
				</button>
			</view>

			<view class="history-drawer" :class="{ active: showHistory }" @click="showHistory = false">
				<view class="drawer-content glass-panel" @click.stop>
					<view class="drawer-header">
						<text class="drawer-title">历史对话</text>
						<text class="close-btn" @click="showHistory = false">×</text>
					</view>
					<scroll-view scroll-y class="session-list">
						<view
							v-for="session in sessions"
							:key="session.session_id"
							class="session-item"
							:class="{ active: currentSessionId === session.session_id }"
							@click="switchSession(session)"
						>
							<view class="session-icon">
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">
									<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
								</svg>
							</view>
							<view class="session-info">
								<text class="session-name">{{ session.title || '新对话' }}</text>
								<text class="session-date">{{ formatDate(session.updated_at) }}</text>
							</view>
						</view>
						<view v-if="sessions.length === 0" class="empty-sessions">
							<text>暂无历史记录</text>
						</view>
					</scroll-view>
				</view>
			</view>
		</view>
	</PageLayout>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { sendMessage, createSession, getLatestSession, getModels, getSessions, getSession, exportSession, generateReport } from '@/services/aiChat';
import PageLayout from '@/components/PageLayout.vue';

const messages = ref([
	{
		role: 'assistant',
		content: '你好，我是你的 AI 运动助手。你可以问我动作要点、训练计划或作业建议。'
	}
]);
const inputText = ref('');
const sending = ref(false);
const reportLoading = ref(false);
const exporting = ref(false);
const scrollTop = ref(0);
const currentSessionId = ref(null);
const showHistory = ref(false);
const sessions = ref([]);
const modelNames = ref(['Qwen']);
const selectedModel = ref('Qwen');

const formatDateKey = (date) => {
	const y = date.getFullYear();
	const m = String(date.getMonth() + 1).padStart(2, '0');
	const d = String(date.getDate()).padStart(2, '0');
	return `${y}-${m}-${d}`;
};

const buildLocalSessionMarkdown = () => {
	return messages.value
		.map((msg) => {
			const role = msg.role === 'user' ? '用户' : '助手';
			return `## ${role}\n\n${msg.content}\n`;
		})
		.join('\n---\n\n');
};

const downloadMarkdown = (content, fileName) => {
	// #ifdef H5
	const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = fileName;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
	// #endif

	// #ifndef H5
	uni.setClipboardData({
		data: content,
		success: () => uni.showToast({ title: '已复制Markdown内容', icon: 'none' })
	});
	// #endif
};

const loadModels = async () => {
	try {
		const res = await getModels();
		if (res.success && Array.isArray(res.data)) {
			const names = res.data.map((m) => m?.name || m?.id || m).filter(Boolean);
			if (names.length > 0) {
				modelNames.value = names;
				if (!names.includes(selectedModel.value)) {
					selectedModel.value = names[0];
				}
			}
		}
	} catch (err) {
		console.error('load models error', err);
	}
};

const fetchSessions = async () => {
	const user = uni.getStorageSync('user');
	if (!user?.id) return;
	try {
		const resList = await getSessions(user.id);
		if (resList.success && Array.isArray(resList.data)) {
			sessions.value = resList.data;
		}
	} catch (err) {
		console.error('fetch sessions error', err);
	}
};

const toggleHistory = () => {
	showHistory.value = !showHistory.value;
	if (showHistory.value) fetchSessions();
};

const handleModelChange = (e) => {
	selectedModel.value = modelNames.value[e.detail.value];
};

const startNewChat = async () => {
	const user = uni.getStorageSync('user');
	if (!user?.id) return;

	const res = await createSession(user.id, selectedModel.value);
	if (res.success && res.data?.session_id) {
		currentSessionId.value = res.data.session_id;
		messages.value = [
			{
				role: 'assistant',
				content: '新会话已开启。我是你的 AI 运动助手，请问有什么可以帮您的？'
			}
		];
		showHistory.value = false;
		fetchSessions();
	}
};

const switchSession = async (session) => {
	currentSessionId.value = session.session_id;
	selectedModel.value = session.model || selectedModel.value;
	const res = await getSession(session.session_id);
	if (res.success && res.data?.messages) {
		messages.value = res.data.messages.filter((m) => m.role !== 'system');
		if (messages.value.length === 0) {
			messages.value = [{ role: 'assistant', content: '会话加载成功，请继续提问。' }];
		}
	}
	showHistory.value = false;
	scrollToBottom();
};

const formatDate = (dateStr) => {
	if (!dateStr) return '';
	const date = new Date(dateStr);
	return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const initSession = async () => {
	const user = uni.getStorageSync('user');
	if (!user?.id) return;

	const res = await getLatestSession(user.id);
	if (res.success && res.data?.session_id) {
		currentSessionId.value = res.data.session_id;
		selectedModel.value = res.data.model || selectedModel.value;
		if (res.data.messages && res.data.messages.length > 0) {
			messages.value = res.data.messages.filter((m) => m.role !== 'system');
		}
	} else {
		await startNewChat();
	}
	fetchSessions();
};

const handleExportSession = async () => {
	if (!currentSessionId.value || exporting.value) {
		uni.showToast({ title: '请先创建会话', icon: 'none' });
		return;
	}

	exporting.value = true;
	const fileName = `会话_${currentSessionId.value}_${formatDateKey(new Date())}.md`;
	try {
		const result = await exportSession(currentSessionId.value);
		if (result.success && result.tempFilePath) {
			// #ifdef H5
			const link = document.createElement('a');
			link.href = result.tempFilePath;
			link.download = fileName;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			uni.showToast({ title: '会话已导出', icon: 'success' });
			// #endif

			// #ifndef H5
			uni.saveFile({
				tempFilePath: result.tempFilePath,
				success: () => uni.showToast({ title: '会话已保存', icon: 'success' }),
				fail: () => downloadMarkdown(buildLocalSessionMarkdown(), fileName)
			});
			// #endif
			return;
		}

		downloadMarkdown(buildLocalSessionMarkdown(), fileName);
		uni.showToast({ title: result.message || '已导出本地记录', icon: 'none' });
	} catch (err) {
		console.error('export session error', err);
		downloadMarkdown(buildLocalSessionMarkdown(), fileName);
		uni.showToast({ title: '导出失败，已提供本地记录', icon: 'none' });
	} finally {
		exporting.value = false;
	}
};

const handleGenerateWeeklyReport = async () => {
	if (reportLoading.value) return;
	const user = uni.getStorageSync('user') || {};
	if (!user?.id) {
		uni.showToast({ title: '请先登录', icon: 'none' });
		return;
	}

	reportLoading.value = true;
	try {
		const result = await generateReport(user.id);
		if (result.success && result.data?.report) {
			const reportText = result.data.report;
			messages.value.push({
				role: 'assistant',
				content: `以下是你的智能周报：\n\n${reportText}`
			});
			scrollToBottom();
			downloadMarkdown(reportText, `智能运动周报_${formatDateKey(new Date())}.md`);
			uni.showToast({ title: '周报已生成', icon: 'success' });
			return;
		}
		uni.showToast({ title: result.message || '生成失败', icon: 'none' });
	} catch (err) {
		console.error('generate weekly report error', err);
		uni.showToast({ title: '生成失败，请稍后重试', icon: 'none' });
	} finally {
		reportLoading.value = false;
	}
};

const handleSend = async () => {
	if (!inputText.value.trim() || sending.value) return;

	const userMsg = inputText.value.trim();
	inputText.value = '';
	messages.value.push({ role: 'user', content: userMsg });
	scrollToBottom();

	sending.value = true;
	try {
		if (!currentSessionId.value) {
			await initSession();
		}
		const res = await sendMessage(currentSessionId.value, userMsg, selectedModel.value);
		if (res.success && res.data?.response) {
			messages.value.push({ role: 'assistant', content: res.data.response });
		} else if (res.success && res.data?.session?.messages) {
			const serverMsgs = res.data.session.messages.filter((m) => m.role !== 'system');
			if (serverMsgs.length > 0) {
				messages.value = serverMsgs;
			}
		} else {
			messages.value.push({ role: 'assistant', content: '收到你的问题了，我正在整理更准确的回复。' });
		}
		fetchSessions();
	} catch (err) {
		console.error('send message error', err);
		messages.value.push({ role: 'assistant', content: '网络似乎不稳定，请稍后再试。' });
	} finally {
		sending.value = false;
		scrollToBottom();
	}
};

const scrollToBottom = () => {
	nextTick(() => {
		scrollTop.value += 1000;
	});
};

onMounted(() => {
	loadModels();
	initSession();
	scrollToBottom();
});
</script>

<style scoped>
.chat-container {
	flex: 1;
	display: flex;
	flex-direction: column;
	background: transparent;
	position: relative;
}

.chat-header {
	height: 100rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 30rpx;
	margin: 20rpx 24rpx 10rpx;
	border-radius: 20rpx;
	z-index: 10;
}

.header-action {
	width: 60rpx;
	height: 60rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: var(--ink-700);
}

.header-icon {
	width: 44rpx;
	height: 44rpx;
}

.header-center {
	flex: 1;
	display: flex;
	justify-content: center;
}

.model-selector {
	display: flex;
	align-items: center;
	padding: 10rpx 24rpx;
	background: rgba(29, 99, 255, 0.08);
	border-radius: 999rpx;
	border: 1rpx solid rgba(29, 99, 255, 0.2);
}

.model-name {
	font-size: 26rpx;
	font-weight: 700;
	color: var(--brand-500);
	margin-right: 8rpx;
}

.chevron-icon {
	width: 24rpx;
	height: 24rpx;
	color: var(--brand-500);
}

.action-strip {
	display: flex;
	gap: 14rpx;
	padding: 0 24rpx 10rpx;
}

.strip-btn {
	flex: 1;
	height: 62rpx;
	line-height: 62rpx;
	border-radius: 999rpx;
	font-size: 24rpx;
	font-weight: 600;
	background: #eef3ff;
	color: #3054aa;
}

.strip-btn[disabled] {
	opacity: 0.55;
}

.message-list {
	flex: 1;
	padding: 24rpx;
}

.message-wrapper {
	display: flex;
	align-items: flex-start;
	gap: 14rpx;
	margin-bottom: 20rpx;
}

.message-wrapper.user {
	flex-direction: row-reverse;
}

.avatar {
	width: 68rpx;
	height: 68rpx;
	border-radius: 34rpx;
	background: rgba(255, 255, 255, 0.95);
	border: 1rpx solid #e4ebfb;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 18rpx rgba(24, 53, 114, 0.08);
}

.icon-inner {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.content-box {
	max-width: 76%;
	padding: 18rpx 20rpx;
	border-radius: 20rpx;
	background: rgba(255, 255, 255, 0.93);
	border: 1rpx solid #e4ebfb;
	box-shadow: 0 8rpx 18rpx rgba(24, 53, 114, 0.08);
}

.user .content-box {
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	border: none;
	box-shadow: 0 10rpx 22rpx rgba(29, 99, 255, 0.28);
}

.content {
	font-size: 25rpx;
	line-height: 1.65;
	color: #24365d;
}

.user .content {
	color: #fff;
}

.padding-bottom {
	height: 130rpx;
}

.input-area {
	position: relative;
	background: rgba(255, 255, 255, 0.94);
	border-top: 1rpx solid #e6ecfb;
	padding: 18rpx 20rpx;
	padding-bottom: calc(env(safe-area-inset-bottom) + 12rpx);
	display: flex;
	align-items: flex-end;
	gap: 14rpx;
}

.message-input {
	flex: 1;
	min-height: 44rpx;
	max-height: 220rpx;
	padding: 14rpx 18rpx;
	font-size: 26rpx;
	line-height: 1.5;
	color: #223357;
	border-radius: 16rpx;
	background: #f3f7ff;
	border: 2rpx solid #e0e8fc;
}

.send-btn {
	width: 122rpx;
	height: 78rpx;
	line-height: 78rpx;
	border-radius: 16rpx;
	font-size: 26rpx;
	font-weight: 700;
	color: #fff;
	background: linear-gradient(120deg, #1d63ff 0%, #23b9ff 100%);
	box-shadow: 0 10rpx 20rpx rgba(29, 99, 255, 0.28);
}

.send-btn[disabled] {
	opacity: 0.55;
}

.history-drawer {
	position: absolute;
	inset: 0;
	background: rgba(0, 0, 0, 0.3);
	z-index: 100;
	opacity: 0;
	visibility: hidden;
	transition: all 0.3s ease;
}

.history-drawer.active {
	opacity: 1;
	visibility: visible;
}

.drawer-content {
	position: absolute;
	top: 0;
	left: -500rpx;
	width: 500rpx;
	height: 100%;
	background: #fff;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	display: flex;
	flex-direction: column;
	box-shadow: 10rpx 0 30rpx rgba(0, 0, 0, 0.1);
}

.history-drawer.active .drawer-content {
	left: 0;
}

.drawer-header {
	padding: 40rpx 30rpx;
	display: flex;
	justify-content: space-between;
	align-items: center;
	border-bottom: 1rpx solid #f0f4ff;
}

.drawer-title {
	font-size: 32rpx;
	font-weight: 700;
	color: var(--ink-900);
}

.close-btn {
	font-size: 48rpx;
	color: var(--ink-500);
	line-height: 1;
}

.session-list {
	flex: 1;
	padding: 20rpx;
}

.session-item {
	display: flex;
	align-items: center;
	padding: 24rpx;
	border-radius: 16rpx;
	margin-bottom: 16rpx;
	transition: all 0.2s ease;
}

.session-item.active {
	background: rgba(29, 99, 255, 0.08);
}

.session-icon {
	width: 40rpx;
	height: 40rpx;
	margin-right: 20rpx;
	color: var(--ink-500);
}

.session-item.active .session-icon {
	color: var(--brand-500);
}

.session-info {
	flex: 1;
	overflow: hidden;
}

.session-name {
	display: block;
	font-size: 28rpx;
	font-weight: 600;
	color: var(--ink-900);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.session-date {
	font-size: 22rpx;
	color: var(--ink-500);
}

.empty-sessions {
	padding: 100rpx 0;
	text-align: center;
	font-size: 26rpx;
	color: var(--ink-500);
}
</style>