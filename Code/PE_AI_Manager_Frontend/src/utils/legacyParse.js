/**
 * 后端遗留接口以「\t\r」分隔、按固定位置拼接字段返回数据，
 * 这里集中处理解析，避免各页面各自手写导致空字段错位、NULL 哨兵混入等问题。
 *
 * 设计约束（保持纯粹，勿掺业务）：
 * - 只做「原始字符串 -> 标准对象」一件事，返回后端原样字段，不改名、不补充、不格式化。
 * - 不接受 role / page / mode 等业务 flag。调用方拿到标准对象后自行拼装展示。
 * - 不过滤空字段（空字段必须保留占位，否则后续字段会整体左移而错位）。
 */

/** 按 \t\r 拆分一条记录，仅去除尾随分隔符，保留中间空字段占位。 */
export const splitLegacyRecord = (raw) => {
  if (raw == null) return []
  return String(raw).replace(/(\t\r)+$/g, '').split('\t\r')
}

/**
 * 将 \t\r 分隔的 ID 列表解析为数组，排除空值与后端的 "NULL" 哨兵。
 * 适用于 get_*_id_by_* 这类列表接口。
 */
export const parseLegacyIdList = (raw) => {
  if (raw == null || String(raw).trim() === 'NULL') return []
  return String(raw)
    .split('\t\r')
    .map((s) => s.trim())
    .filter((s) => s && s !== 'NULL')
}

/**
 * 解析课程信息（来自 /Course/get_info_by_course_id）。
 * 后端返回顺序: 教师id \t\r 课程名 \t\r 描述 \t\r 课程码 \t\r 学期 \t\r 是否激活 \t\r 创建时间
 * 注意：课号(课程号)不在返回串里，它就是课程主键 id，需由调用方传入。
 *
 * @param {string} raw 后端返回的原始字符串
 * @param {string} courseId 课程主键（即课号）
 * @returns {{id,teacherId,name,info,code,semester,isActive,createdTime}}
 */
export const parseCourseInfo = (raw, courseId = '') => {
  const d = splitLegacyRecord(raw)
  return {
    id: courseId,
    teacherId: d[0] || '',
    name: d[1] || '',
    info: d[2] || '',
    code: d[3] || '',
    semester: d[4] || '',
    isActive: d[5] || '',
    createdTime: d[6] || ''
  }
}

/**
 * 解析作业信息（来自 /Homework/get_info_by_homework_id）。
 * 后端返回顺序: 标题 \t\r 描述 \t\r 截止日期 \t\r 创建时间
 *
 * @param {string} raw 后端返回的原始字符串
 * @param {string} homeworkId 作业主键
 * @returns {{id,title,description,deadline,createTime}}
 */
export const parseHomeworkInfo = (raw, homeworkId = '') => {
  const d = splitLegacyRecord(raw)
  return {
    id: homeworkId,
    title: d[0] || '',
    description: d[1] || '',
    deadline: d[2] || '',
    createTime: d[3] || ''
  }
}
