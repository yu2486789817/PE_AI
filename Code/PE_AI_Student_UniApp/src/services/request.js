// 本地测试服务器地址
// 真机调试时需改为电脑局域网 IP（如 192.168.x.x）
// Render 部署完成后，把云端 HTTPS 域名填到这里。
const DEVTOOLS_HOST = 'localhost';
const CLOUD_HOST = 'https://pe-ai-backend-9869.onrender.com';
const DEVICE_HOST = '100.80.35.77';

// 服务端口映射（与 vite.config.js 代理配置一致）
const SERVICE_MAP = {
	'/chat': 5000,   // AIChat - AI 聊天助手
	'/video': 8000,  // Yolo_backend - 视频处理
};

const DEFAULT_PORT = 5001; // Spring Boot 后端

const getServicePrefix = (url) => Object.keys(SERVICE_MAP).find((prefix) => url.startsWith(prefix)) || '';

const getServerHost = () => {
	if (CLOUD_HOST) return CLOUD_HOST;

	// #ifdef MP-WEIXIN
	const platform = uni.getDeviceInfo ? uni.getDeviceInfo().platform : '';
	if (platform === 'devtools' || platform === 'windows' || platform === 'mac') {
		return DEVTOOLS_HOST;
	}
	// #endif

	return CLOUD_HOST || DEVICE_HOST;
};

const getBaseURL = (url) => {
	// #ifdef H5
	return ''; // H5 通过 vite.config.js 代理，无需指定基地址
	// #endif

	// #ifndef H5
	const prefix = getServicePrefix(url);
	const port = SERVICE_MAP[prefix] || DEFAULT_PORT;
	const host = getServerHost();
	if (host.startsWith('http://') || host.startsWith('https://')) {
		return host;
	}
	return `http://${host}:${port}`;
	// #endif
};

const getRequestPath = (url) => {
	const prefix = getServicePrefix(url);
	if (!prefix) return url;
	const host = getServerHost();
	if (host.startsWith('http://') || host.startsWith('https://')) return url;
	return url.slice(prefix.length) || '/';
};

const buildURL = (url) => getBaseURL(url) + getRequestPath(url);

const request = (options) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: buildURL(options.url),
			method: options.method || 'GET',
			data: options.data,
			timeout: 30000, // Render 免费服务冷启动时首次请求可能超过 8 秒
			header: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${uni.getStorageSync('token')}`,
				...options.header
			},
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve(res);
				} else {
					if (res.statusCode === 401) {
						uni.removeStorageSync('token');
						uni.reLaunch({ url: '/pages/login/login' });
					}
					reject(res);
				}
			},
			fail: (err) => {
				reject(err);
			}
		});
	});
};

export default {
	get: (url, data) => request({ url, method: 'GET', data }),
	post: (url, data) => request({ url, method: 'POST', data }),
	delete: (url) => request({ url, method: 'DELETE' }),
	buildURL,
};
