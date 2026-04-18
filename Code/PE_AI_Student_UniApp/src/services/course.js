import request from './request';

export const getStudentCourses = async (studentId) => {
	try {
		const response = await request.post('/Course_student/get_course_id_by_student', {
			first: studentId
		});
		if (response.data && response.data.data && response.data.data !== 'NULL') {
			const courseIds = response.data.data.split('\t\r');
			const courses = [];
			for (const courseId of courseIds) {
				const courseResp = await request.post('/Course/get_info_by_course_id', {
					first: courseId
				});
				if (courseResp.data && courseResp.data.data) {
					const parts = courseResp.data.data.split('\t\r');
					courses.push({
						id: courseId,
						teacherId: parts[0] || '',
						name: parts[1] || '',
						info: parts[2] || '',
						code: parts[3] || '',
						semester: parts[4] || '',
						isActive: parts[5] || '1',
						createdTime: parts[6] || ''
					});
				}
			}
			return { success: true, data: courses };
		}
		return { success: true, data: [] };
	} catch (error) {
		console.error('获取课程列表失败:', error);
		return { success: false, message: '获取课程列表失败' };
	}
};

export const joinCourse = async (studentId, courseCode) => {
	try {
		const response = await request.post('/Course_student/add_course', {
			first: studentId,
			third: courseCode
		});
		return { success: response.data && response.data.code >= 0, data: response.data };
	} catch (error) {
		console.error('加入课程失败:', error);
		return { success: false, message: '加入课程失败，课程码可能不正确' };
	}
};

export const getCourseInfo = async (courseId) => {
	try {
		const response = await request.post('/Course/get_info_by_course_id', {
			first: courseId
		});
		if (response.data && response.data.data) {
			const parts = response.data.data.split('\t\r');
			return {
				success: true,
				data: {
					id: courseId,
					teacherId: parts[0] || '',
					name: parts[1] || '',
					info: parts[2] || '',
					code: parts[3] || '',
					semester: parts[4] || '',
					isActive: parts[5] || '1',
					createdTime: parts[6] || ''
				}
			};
		}
		return { success: false, message: '获取课程信息失败' };
	} catch (error) {
		console.error('获取课程信息失败:', error);
		return { success: false, message: '获取课程信息失败' };
	}
};

export default {
	getStudentCourses,
	joinCourse,
	getCourseInfo
};
