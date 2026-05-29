import request from './request';

const getToken = () => {
	const token = uni.getStorageSync('token');
	if (token) return token;
	const user = uni.getStorageSync('user') || {};
	return user.token || '';
};

const isSubmitted = async (homeworkId, studentId, token) => {
	const resp = await request.post('/Homework/get_submit_id_by_student', {
		first: '0',
		second: studentId,
		third: token,
		fourth: String(homeworkId),
		fifth: studentId
	});
	const value = String(resp.data?.data || '').trim();
	return !!(resp.data?.success && value && !['NULL', '-1', '-2'].includes(value));
};

export const getStudentAssignments = async (studentId) => {
	try {
		const token = getToken();
		const courseResp = await request.post('/Course_student/get_course_id_by_student', {
			first: studentId,
			second: token
		});

		if (!courseResp.data || !courseResp.data.data || courseResp.data.data === 'NULL') {
			return { success: true, data: [] };
		}

		const courseIds = courseResp.data.data.split('\t\r').filter(Boolean);
		const allAssignments = [];
		const courseNameMap = {};

		for (const courseId of courseIds) {
			if (!courseNameMap[courseId]) {
				try {
					const courseDetailResp = await request.post('/Course/get_info_by_course_id', {
						first: courseId,
						second: token
					});
					if (courseDetailResp.data?.success && courseDetailResp.data?.data) {
						const courseParts = courseDetailResp.data.data.split('\t\r');
						courseNameMap[courseId] = courseParts[1] || '';
					} else {
						courseNameMap[courseId] = '';
					}
				} catch (e) {
					courseNameMap[courseId] = '';
				}
			}

			const hwResp = await request.post('/Homework/get_homework_id_by_course', {
				first: '0',
				second: studentId,
				third: token,
				fourth: courseId
			});

			if (hwResp.data && hwResp.data.data && hwResp.data.data !== 'NULL') {
				const hwIds = hwResp.data.data.split('\t\r').map(s => s.trim()).filter(s => s && s !== 'NULL');
				for (const hwId of hwIds) {
					const detailResp = await request.post('/Homework/get_info_by_homework_id', {
						first: courseId,
						second: hwId
					});

					if (detailResp.data && detailResp.data.data) {
						const parts = detailResp.data.data.split('\t\r');
						const deadline = parts[2] || '';
						let statusText = '进行中';
						try {
							if (await isSubmitted(hwId.trim(), studentId, token)) {
								statusText = '已完成';
							} else if (deadline && new Date(deadline) < new Date()) {
								statusText = '已截止';
							}
						} catch (e) {
							if (deadline && new Date(deadline) < new Date()) {
								statusText = '已截止';
							}
						}
						allAssignments.push({
							id: parseInt(hwId.trim(), 10),
							courseId,
							courseName: courseNameMap[courseId] || '',
							title: parts[0] || '',
							description: parts[1] || '',
							deadline,
							createTime: parts[3] || '',
							statusText
						});
					}
				}
			}
		}

		return { success: true, data: allAssignments };
	} catch (error) {
		console.error('获取作业列表失败:', error);
		return { success: false, message: '获取作业列表失败' };
	}
};

export const getAssignmentDetail = async (homeworkId, courseId) => {
	try {
		const response = await request.post('/Homework/get_info_by_homework_id', {
			first: courseId,
			second: homeworkId
		});

		if (response.data && response.data.data) {
			const parts = response.data.data.split('\t\r');
			return {
				success: true,
				data: {
					id: parseInt(homeworkId, 10),
					courseId,
					title: parts[0] || '',
					description: parts[1] || '',
					deadline: parts[2] || '',
					createTime: parts[3] || ''
				}
			};
		}
		return { success: false, message: '获取作业详情失败' };
	} catch (error) {
		console.error('获取作业详情失败:', error);
		return { success: false, message: '获取作业详情失败' };
	}
};

export const submitHomework = async (homeworkId, studentId, videoUrl, courseId = '') => {
	try {
		const token = getToken();
		const response = await request.post('/Homework/submit_homework', {
			first: studentId,
			second: token,
			third: courseId,
			fourth: String(homeworkId),
			fifth: videoUrl
		});

		if (response.data && response.data.success) {
			return { success: true, data: response.data.data };
		}
		return { success: false, message: '提交失败' };
	} catch (error) {
		console.error('提交作业失败:', error);
		return { success: false, message: '提交作业失败' };
	}
};

export const getSubmissionHistory = async (homeworkId, studentId) => {
	try {
		const token = getToken();
		const response = await request.post('/Homework/get_submit_id_by_student', {
			first: '0',
			second: studentId,
			third: token,
			fourth: String(homeworkId),
			fifth: studentId
		});

		if (!response.data || !response.data.data || response.data.data === 'NULL') {
			return { success: true, data: [] };
		}

		const submitIds = response.data.data.split('\t\r').filter(Boolean);
		const submissions = [];

		for (const submitId of submitIds) {
			const detailResp = await request.post('/Homework/get_submit_info', {
				first: '0',
				second: studentId,
				third: token,
				fourth: submitId
			});

			if (detailResp.data && detailResp.data.data) {
				const parts = detailResp.data.data.split('\t\r');
				submissions.push({
					id: parseInt(submitId, 10),
					videoUrl: parts[0] || '',
					score: parts[1] ? parseFloat(parts[1]) : null,
					aiFeedback: parts[2] || '',
					teacherFeedback: parts[3] || '',
					createTime: parts[4] || ''
				});
			}
		}

		return { success: true, data: submissions };
	} catch (error) {
		console.error('获取提交历史失败:', error);
		return { success: false, message: '获取提交历史失败' };
	}
};

export const getAIFeedback = async (submissionId, studentId = '') => {
	try {
		const token = getToken();
		const response = await request.post('/Homework/get_submit_info', {
			first: '0',
			second: studentId,
			third: token,
			fourth: String(submissionId)
		});

		if (response.data && response.data.data) {
			const parts = response.data.data.split('\t\r');
			return {
				success: true,
				data: {
					videoUrl: parts[0] || '',
					score: parts[1] ? parseFloat(parts[1]) : null,
					aiFeedback: parts[2] || '',
					teacherFeedback: parts[3] || '',
					createTime: parts[4] || ''
				}
			};
		}
		return { success: false, message: '获取AI反馈失败' };
	} catch (error) {
		console.error('获取AI反馈失败:', error);
		return { success: false, message: '获取AI反馈失败' };
	}
};

export default {
	getStudentAssignments,
	getAssignmentDetail,
	submitHomework,
	getSubmissionHistory,
	getAIFeedback
};
