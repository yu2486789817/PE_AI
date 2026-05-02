import apiClient from './axios';
import SHA256 from 'crypto-js/sha256';

const parseLegacyInfoPayload = (raw, keys) => {
  const text = typeof raw === 'string' ? raw : '';
  const parts = text ? text.split('\t\r') : [];
  const mapped = {};
  keys.forEach((key, index) => {
    mapped[key] = parts[index] || '';
  });
  return mapped;
};

const resolveActiveToken = (jwt) => {
  const storageToken = (localStorage.getItem('token') || '').trim();
  const bodyToken = typeof jwt === 'string' ? jwt.trim() : '';
  return storageToken || bodyToken;
};

const handleApiError = (error, operationType) => {
  if (error.response) {
    const errorCode = error.response.data?.error_code ?? error.response.data?.code ?? -99;

    const specificErrors = {
      '-10': { password_change: '参数错误' },
      '-11': { password_change: '查询用户是否存在失败' },
      '-12': { password_change: '查询用户密码失败' },
      '-13': { password_change: '修改用户密码失败' },
      '-21': {
        login: '用户不存在',
        register: '该用户已经注册过账号',
        password_change: '账号不存在'
      },
      '-22': {
        login: '账号无效',
        register: '该ID不在基准库内，无效',
        password_change: '账号信息异常'
      },
      '-23': {
        login: '登录密码输入错误',
        register: '密码格式错误',
        password_change: '输入的旧密码不正确'
      }
    };

    if (specificErrors[errorCode] && specificErrors[errorCode][operationType]) {
      return {
        success: false,
        error_code: errorCode,
        message: specificErrors[errorCode][operationType]
      };
    }

    let genericMessage = '操作失败';
    if (operationType === 'login') genericMessage = '登录失败';
    if (operationType === 'register') genericMessage = '注册失败';
    if (operationType === 'password_change') genericMessage = '密码修改失败';
    if (operationType === 'get_info') genericMessage = '获取信息失败';
    return { success: false, error_code: errorCode, message: genericMessage };
  }

  if (error.request) {
    let genericMessage = '操作失败';
    if (operationType === 'login') genericMessage = '登录失败';
    if (operationType === 'register') genericMessage = '注册失败';
    if (operationType === 'password_change') genericMessage = '密码修改失败';
    if (operationType === 'get_info') genericMessage = '获取信息失败';
    return { success: false, error_code: -99, message: genericMessage };
  }

  let genericMessage = '操作失败';
  if (operationType === 'login') genericMessage = '登录失败';
  if (operationType === 'register') genericMessage = '注册失败';
  if (operationType === 'password_change') genericMessage = '密码修改失败';
  if (operationType === 'get_info') genericMessage = '获取信息失败';
  return { success: false, error_code: -99, message: genericMessage };
};

const sha256 = async (str) => SHA256(str).toString();

export const loginTeacher = async (teacher_id, password) => {
  try {
    const passwordHash = await sha256(password);
    const requestData = { first: teacher_id, second: passwordHash };
    const response = await apiClient.post('/User/login_teacher', requestData);
    const loginData = response.data;
    if (loginData?.data) {
      localStorage.setItem('token', loginData.data);
    }
    return { success: true, data: loginData };
  } catch (error) {
    return handleApiError(error, 'login');
  }
};

export const loginStudent = async (student_id, password) => {
  try {
    const passwordHash = await sha256(password);
    const requestData = { first: student_id, second: passwordHash };
    const response = await apiClient.post('/User/login_student', requestData);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'login');
  }
};

export const registerTeacher = async (id, password, name, gender, title, college, department) => {
  try {
    const passwordHash = await sha256(password);
    const response = await apiClient.post('/User/new_teacher', {
      first: id,
      second: passwordHash,
      third: name,
      fourth: gender,
      fifth: title,
      sixth: college,
      seventh: department
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'register');
  }
};

export const registerStudent = async (id, password, name, gender, major, college, department) => {
  try {
    const passwordHash = await sha256(password);
    const response = await apiClient.post('/User/new_student', {
      first: id,
      second: passwordHash,
      third: name,
      fourth: gender,
      fifth: major,
      sixth: college,
      seventh: department
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'register');
  }
};

export const changeTeacherPassword = async (id, oldPassword, newPassword) => {
  try {
    const oldPasswordHash = await sha256(oldPassword);
    const newPasswordHash = await sha256(newPassword);
    const response = await apiClient.post('/User/change_teacher_password', {
      first: id,
      second: oldPasswordHash,
      third: newPasswordHash
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'password_change');
  }
};

export const changeStudentPassword = async (id, oldPassword, newPassword) => {
  try {
    const oldPasswordHash = await sha256(oldPassword);
    const newPasswordHash = await sha256(newPassword);
    const response = await apiClient.post('/User/change_student_password', {
      first: id,
      second: oldPasswordHash,
      third: newPasswordHash
    });
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'password_change');
  }
};

export const changeTeacherInfo = async (id, jwt, name, gender, title, college, department) => {
  const requestBody = {
    first: id,
    second: jwt,
    third: name,
    fourth: gender,
    fifth: title,
    sixth: college,
    seventh: department
  };

  try {
    const response = await apiClient.post('/User/change_teacher_info', requestBody);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'info_change');
  }
};

export const changeStudentInfo = async (id, jwt, name, gender, major, college, department) => {
  const requestBody = {
    first: id,
    second: jwt,
    third: name,
    fourth: gender,
    fifth: major,
    sixth: college,
    seventh: department
  };

  try {
    const response = await apiClient.post('/User/change_student_info', requestBody);
    return { success: true, data: response.data };
  } catch (error) {
    return handleApiError(error, 'info_change');
  }
};

export const getTeacherInfo = async (id, jwt, userType, teacherId) => {
  const activeToken = resolveActiveToken(jwt);
  const requestBody = {
    first: id,
    second: activeToken,
    third: userType,
    fourth: teacherId
  };

  try {
    const response = await apiClient.post('/User/get_teacher_info', requestBody);

    if (!response.data?.success) {
      return {
        success: false,
        error_code: response.data?.code ?? -99,
        message: response.data?.message || '获取教师个人信息失败'
      };
    }

    const data = parseLegacyInfoPayload(response.data?.data, [
      'name',
      'gender',
      'title',
      'college',
      'department'
    ]);

    return { success: true, data };
  } catch (error) {
    return handleApiError(error, 'get_info');
  }
};

export const getStudentInfo = async (id, jwt, userType, studentId) => {
  const activeToken = resolveActiveToken(jwt);
  const requestBody = {
    first: id,
    second: activeToken,
    third: userType,
    fourth: studentId
  };

  try {
    const response = await apiClient.post('/User/get_student_info', requestBody);

    if (!response.data?.success) {
      return {
        success: false,
        error_code: response.data?.code ?? -99,
        message: response.data?.message || '获取学生个人信息失败'
      };
    }

    const data = parseLegacyInfoPayload(response.data?.data, [
      'name',
      'gender',
      'major',
      'college',
      'department'
    ]);

    return { success: true, data };
  } catch (error) {
    return handleApiError(error, 'get_info');
  }
};

export default {
  loginTeacher,
  loginStudent,
  registerTeacher,
  registerStudent,
  changeTeacherPassword,
  changeStudentPassword,
  changeTeacherInfo,
  changeStudentInfo,
  getTeacherInfo,
  getStudentInfo
};
