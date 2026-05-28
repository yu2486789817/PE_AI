<script>
export default {
	onLaunch() {
		const user = uni.getStorageSync('user')
		if (!user) {
			uni.reLaunch({ url: '/pages/login/login' })
		}
	},
	onShow() {},
	onHide() {}
}
</script>

<style>
:root {
	--color-primary-500: #236df2;
	--color-primary-600: #1d5fdd;
	--color-primary-700: #1a4dac;
	--color-success-500: #139769;
	--color-success-600: #0f8059;
	--color-warning-500: #ea8814;
	--color-warning-600: #c16e10;
	--color-danger-500: #d63e35;
	--color-danger-600: #b4322a;
	--color-ink-900: #172033;
	--color-ink-800: #22304a;
	--color-ink-700: #2b3851;
	--color-ink-600: #44516e;
	--color-ink-500: #67748f;
	--color-line-200: #d8e0ee;
	--color-line-100: #e8edf7;
	--color-surface-card: #ffffff;
	--color-surface-100: #f7f9fe;
	--color-surface-200: #eff3fb;
	--radius-xl: 28rpx;
	--radius-lg: 22rpx;
	--radius-md: 16rpx;
	--shadow-card: 0 10rpx 24rpx rgba(23, 56, 122, 0.1);
	--shadow-soft: 0 18rpx 40rpx rgba(15, 44, 96, 0.14);
	--tabbar-height: 110rpx;
	--safe-area-bottom: env(safe-area-inset-bottom);
	--page-bottom-padding: calc(var(--tabbar-height) + var(--safe-area-bottom) + 30rpx);
	font-family: 'Avenir Next', 'PingFang SC', 'Noto Sans SC', sans-serif;
}

page,
body {
	background: radial-gradient(circle at 10% 10%, rgba(35, 109, 242, 0.14), transparent 35%),
		radial-gradient(circle at 90% 5%, rgba(64, 172, 245, 0.1), transparent 30%),
		linear-gradient(180deg, #f9fbff 0%, #f1f5fd 100%);
	color: var(--color-ink-900);
	min-height: 100vh;
	font-size: 28rpx;
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
	display: flex;
	align-items: center;
	justify-content: center;
	box-sizing: border-box;
}

button::after {
	border: none;
}

.btn-primary {
	height: 80rpx;
	line-height: 80rpx;
	padding: 0 28rpx;
	border-radius: 999rpx;
	font-size: 26rpx;
	font-weight: 700;
	color: #fff;
	background: linear-gradient(120deg, var(--color-primary-500) 0%, #2f94f5 100%);
	box-shadow: 0 12rpx 24rpx rgba(35, 109, 242, 0.3);
}

.btn-primary[disabled] {
	color: #ffffff;
	background: linear-gradient(120deg, #9fbff8 0%, #a8d6fb 100%);
	box-shadow: 0 10rpx 22rpx rgba(35, 109, 242, 0.16);
	opacity: 1;
}

.btn-outline {
	height: 76rpx;
	line-height: 76rpx;
	padding: 0 24rpx;
	border-radius: 999rpx;
	font-size: 24rpx;
	font-weight: 600;
	color: var(--color-ink-700);
	background: var(--color-surface-card);
	border: 2rpx solid var(--color-line-200);
}

.btn-outline[disabled] {
	color: #8a96ad;
	background: #eef3fb;
	border-color: #d8e0ee;
	opacity: 1;
}

.input-base {
	height: 84rpx;
	padding: 0 20rpx;
	border-radius: var(--radius-md);
	font-size: 26rpx;
	background: var(--color-surface-card);
	border: 2rpx solid var(--color-line-200);
	color: var(--color-ink-900);
}

.textarea-base {
	padding: 16rpx 20rpx;
	border-radius: var(--radius-md);
	font-size: 24rpx;
	line-height: 1.6;
	background: var(--color-surface-card);
	border: 2rpx solid var(--color-line-200);
	color: var(--color-ink-900);
}

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
</style>
