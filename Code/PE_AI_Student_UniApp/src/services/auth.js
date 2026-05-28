import request from './request';
import CryptoJS from 'crypto-js';

const sha256 = (str) => CryptoJS.SHA256(str).toString();
const splitLegacyFields = (raw) => (raw || '').split('\t\r');

export const buildStudentUser = (id, rawInfo = '') => {
	const parts = splitLegacyFields(rawInfo);
	return {
		id,
		role: 'student',
		name: parts[0] || '',
		gender: parts[1] || '',
		major: parts[2] || '',
		college: parts[3] || '',
		department: parts[4] || ''
	};
};

export const loginStudent = async (student_id, password) => {
	try {
		const passwordHash = sha256(password);
		const response = await request.post('/User/login_student', {
			first: student_id,
			second: passwordHash
		});

		if (response.data?.success && response.data.data) {
			const jwt = response.data.data;
			uni.setStorageSync('token', jwt);
			uni.setStorageSync('lastStudentId', student_id);
			const baseUser = { id: student_id, role: 'student' };
			uni.setStorageSync('user', baseUser);
			try {
				const infoResp = await getStudentInfo(student_id, jwt, student_id);
				if (infoResp?.data?.success && infoResp.data.data) {
					uni.setStorageSync('user', buildStudentUser(student_id, infoResp.data.data));
				}
			} catch (e) {
			}
		} else {
			return { success: false, message: response.data?.message || '登录失败，请检查账号密码' };
		}
		return { success: true, data: response.data };
	} catch (error) {
		console.error('登录失败:', error);
		return { success: false, message: '登录失败，请检查账号密码' };
	}
};

export const registerStudent = async (studentData) => {
	try {
		const passwordHash = sha256(studentData.password);
		const response = await request.post('/User/new_student', {
			first: studentData.id,
			second: passwordHash,
			third: studentData.name,
			fourth: studentData.gender,
			fifth: studentData.major,
			sixth: studentData.college,
			seventh: studentData.department
		});
		return { success: true, data: response.data };
	} catch (error) {
		console.error('注册失败:', error);
		return { success: false, message: '注册失败，请检查信息是否正确' };
	}
};

export const changePassword = async (studentId, oldPassword, newPassword) => {
	try {
		const oldHash = sha256(oldPassword);
		const newHash = sha256(newPassword);
		const response = await request.post('/User/change_student_password', {
			first: studentId,
			second: oldHash,
			third: newHash
		});
		return { success: true, data: response.data };
	} catch (error) {
		console.error('修改密码失败:', error);
		return { success: false, message: '修改密码失败' };
	}
};

export const updateStudentInfo = async (studentData) => {
	try {
		const response = await request.post('/User/change_student_info', {
			first: studentData.id,
			third: studentData.name,
			fourth: studentData.gender,
			fifth: studentData.major,
			sixth: studentData.college,
			seventh: studentData.department
		});
		return { success: true, data: response.data };
	} catch (error) {
		console.error('更新信息失败:', error);
		return { success: false, message: '更新信息失败' };
	}
};

export const logout = () => {
	uni.removeStorageSync('token');
	uni.removeStorageSync('user');
	uni.removeStorageSync('lastStudentId');
	uni.reLaunch({ url: '/pages/login/login' });
};

export const getStudentInfo = async (id, jwt, studentId) => {
	return request.post('/User/get_student_info', {
		first: id,
		second: jwt,
		third: 'student',
		fourth: studentId
	});
};

export default {
	loginStudent,
	registerStudent,
	changePassword,
	updateStudentInfo,
	logout,
	getStudentInfo,
	buildStudentUser
};
