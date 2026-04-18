<script>
export default {
	onLaunch: function() {
		console.log('App Launch');
		const user = uni.getStorageSync('user');
		if (!user) {
			uni.reLaunch({
				url: '/pages/login/login'
			});
		}
	},
	onShow: function() {
		console.log('App Show');
	},
	onHide: function() {
		console.log('App Hide');
	}
}
</script>

<style>
:root {
	--brand-500: #1d63ff;
	--brand-400: #4d89ff;
	--accent-500: #18b7ff;
	--ink-900: #172033;
	--ink-700: #44516e;
	--ink-500: #6f7a96;
	--line-200: #dbe2f2;
	--line-100: #e9eef9;
	--surface-100: #f8fbff;
	--surface-200: #f2f6ff;
	--surface-card: #ffffff;
	--success-500: #12b981;
	--warning-500: #ff8a00;
	--danger-500: #ef4444;
	--radius-xl: 28rpx;
	--radius-lg: 22rpx;
	--radius-md: 16rpx;
	--shadow-soft: 0 16rpx 40rpx rgba(38, 78, 154, 0.12);
	--shadow-card: 0 8rpx 24rpx rgba(22, 42, 89, 0.08);
	
	/* TabBar & Safe Area */
	--tabbar-height: 110rpx;
	--safe-area-bottom: env(safe-area-inset-bottom);
	--page-bottom-padding: calc(var(--tabbar-height) + var(--safe-area-bottom) + 30rpx);

	font-family: "Inter", "Avenir Next", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

page,
body {
	background:
		radial-gradient(circle at 12% 12%, rgba(77, 137, 255, 0.12), transparent 35%),
		radial-gradient(circle at 88% 8%, rgba(24, 183, 255, 0.1), transparent 30%),
		linear-gradient(180deg, var(--surface-100) 0%, var(--surface-200) 100%);
	color: var(--ink-900);
	min-height: 100vh;
	font-size: 28rpx;
}

/* Page Transition */
.page-fade-enter-active,
.page-fade-leave-active {
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-fade-enter-from {
	opacity: 0;
	transform: translateY(20rpx);
}
.page-fade-leave-to {
	opacity: 0;
	transform: translateY(-20rpx);
}

view,
text,
button,
input,
textarea {
	box-sizing: border-box;
}

button {
	border: none;
	background: transparent;
	padding: 0;
	margin: 0;
	line-height: inherit;
}

button::after {
	border: none;
}

.p-4 {
	padding: 32rpx;
}

.text-blue {
	color: var(--brand-500);
}

/* Common UI Patterns */
.glass-panel {
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(10px);
	-webkit-backdrop-filter: blur(10px);
	border: 1px solid rgba(255, 255, 255, 0.3);
}
</style>
