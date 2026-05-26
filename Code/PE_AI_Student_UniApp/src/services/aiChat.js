import request from './request';

export const getSessions = async (userId) => {
	try {
		const response = await request.get(`/chat/api/sessions?user_id=${userId}`);
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: '获取会话列表失败' };
	} catch (error) {
		console.error('获取会话列表失败:', error);
		return { success: false, message: '获取会话列表失败' };
	}
};

export const getLatestSession = async (userId) => {
	try {
		const response = await request.get(`/chat/api/sessions/user/${userId}`);
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, data: null };
	} catch (error) {
		console.error('获取最新会话失败:', error);
		return { success: false, message: '获取最新会话失败' };
	}
};

export const createSession = async (userId, model = 'peai') => {
	try {
		const response = await request.post('/chat/api/sessions', {
			user_id: userId,
			model
		});
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: '创建会话失败' };
	} catch (error) {
		console.error('创建会话失败:', error);
		return { success: false, message: '创建会话失败' };
	}
};

export const getSession = async (sessionId) => {
	try {
		const response = await request.get(`/chat/api/sessions/${sessionId}`);
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: '获取会话详情失败' };
	} catch (error) {
		console.error('获取会话详情失败:', error);
		return { success: false, message: '获取会话详情失败' };
	}
};

export const sendMessage = async (sessionId, message, model = 'peai') => {
	try {
		const response = await request.post(`/chat/api/sessions/${sessionId}/messages`, {
			message,
			model
		});
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: '发送消息失败' };
	} catch (error) {
		console.error('发送消息失败:', error);
		return { success: false, message: '发送消息失败' };
	}
};

export const deleteSession = async (sessionId) => {
	try {
		const response = await request.delete(`/chat/api/sessions/${sessionId}`);
		if (response.data && response.data.success) {
			return { success: true };
		}
		return { success: false, message: '删除会话失败' };
	} catch (error) {
		console.error('删除会话失败:', error);
		return { success: false, message: '删除会话失败' };
	}
};

export const clearSession = async (sessionId) => {
	try {
		const response = await request.post(`/chat/api/sessions/${sessionId}/clear`);
		if (response.data && response.data.success) {
			return { success: true };
		}
		return { success: false, message: '清空会话失败' };
	} catch (error) {
		console.error('清空会话失败:', error);
		return { success: false, message: '清空会话失败' };
	}
};

export const getModels = async () => {
	try {
		const response = await request.get('/chat/api/models');
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: '获取模型列表失败' };
	} catch (error) {
		console.error('获取模型列表失败:', error);
		return { success: false, message: '获取模型列表失败' };
	}
};

export const exportSession = async (sessionId) => {
	return new Promise((resolve) => {
		uni.downloadFile({
			url: request.buildURL(`/chat/api/sessions/${sessionId}/export`),
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					resolve({ success: true, tempFilePath: res.tempFilePath });
					return;
				}
				resolve({ success: false, message: `导出失败(${res.statusCode})` });
			},
			fail: () => resolve({ success: false, message: '导出失败' })
		});
	});
};

export const generateReport = async (studentId, query = '根据我的情况给出综合分析和下周长期训练建议') => {
	try {
		const response = await request.post('/chat/api/analysis/generate', {
			student_id: studentId,
			analysis_type: 'personalized_tips',
			query
		});
		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: response.data?.error || '生成报告失败' };
	} catch (error) {
		console.error('生成报告失败:', error);
		return { success: false, message: '生成报告失败' };
	}
};

export default {
	getSessions,
	getLatestSession,
	createSession,
	getSession,
	sendMessage,
	deleteSession,
	clearSession,
	getModels,
	exportSession,
	generateReport
};
