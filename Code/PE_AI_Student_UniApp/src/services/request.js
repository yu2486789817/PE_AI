// 基于 uni.request 的简易 Axios 替代方案
const baseURL = ''; // 通过 vite.config.js 代理

const request = (options) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: baseURL + options.url,
			method: options.method || 'GET',
			data: options.data,
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
};
