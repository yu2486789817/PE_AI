package com.pe.ai.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pe.ai.common.Result;
import com.pe.ai.entity.*;
import com.pe.ai.mapper.*;
import com.pe.ai.service.UserService;
import com.pe.ai.util.RequestValueResolver;
import com.pe.ai.util.SecurityUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Legacy-compatible controller matching the original .NET API paths:
 * /Course_student/*, /Course/*, /Homework/*
 *
 * All responses use the old tab-separated string format for frontend compatibility.
 */
@RestController
@RequiredArgsConstructor
public class LegacyCourseController {

    private final CourseMapper courseMapper;
    private final HomeworkMapper homeworkMapper;
    private final SubmitMapper submitMapper;
    private final StudentCourseMapper studentCourseMapper;
    private final StudentMapper studentMapper;
    private final CourseClassMapper courseClassMapper;
    private final AiTypeMapper aiTypeMapper;
    private final UserService userService;

    // Helper to handle both "first" and "First" parameter keys from frontend
    private String getParam(Map<String, String> body, String key) {
        return RequestValueResolver.getIgnoreCase(body, key);
    }

    private String resolveJwt(Map<String, String> body, HttpServletRequest request) {
        return RequestValueResolver.resolveJwt(body, request);
    }

    private boolean isCourseArchived(Course course) {
        return course != null && Integer.valueOf(2).equals(course.getIsActive());
    }

    private Result<Void> rejectIfCourseArchived(Course course) {
        if (isCourseArchived(course)) {
            return Result.error(-22, "Course archived");
        }
        return null;
    }

    private Result<Void> checkLegacyAuth(Map<String, String> body, HttpServletRequest request) {
        String capacity = getParam(body, "capacity");
        String userId = getParam(body, "user_id");
        String jwt = resolveJwt(body, request);

        if (capacity == null) capacity = getParam(body, "first");
        if (userId == null) userId = getParam(body, "second");

        if (capacity != null && userId != null && ("0".equals(capacity.trim()) || "1".equals(capacity.trim()))) {
            return userService.checkJwt(Integer.parseInt(capacity.trim()), userId, jwt);
        }

        String teacherId = getParam(body, "teacher_id");
        if (teacherId == null) teacherId = getParam(body, "first");
        if (teacherId != null && teacherId.trim().matches("\\d{4,}")) {
            Result<Void> teacherAuth = userService.checkJwt(1, teacherId, jwt);
            if (teacherAuth.getCode() >= 0) return teacherAuth;
        }

        String studentId = getParam(body, "student_id");
        if (studentId == null) studentId = getParam(body, "first");
        if (studentId != null && studentId.trim().matches("\\d{4,}")) {
            return userService.checkJwt(0, studentId, jwt);
        }

        // Legacy read-only style calls often send only { first: resourceId, second: jwt }.
        // In that case there is no explicit user id to re-compute the full token hash.
        // We still require a non-expired token timestamp to avoid breaking existing pages.
        if (jwt != null && jwt.length() >= 14) {
            String jwtTime = jwt.substring(0, 14);
            if (!SecurityUtil.isTokenExpired(jwtTime)) {
                return Result.success();
            }
            return Result.error(-24, "JWT TLE");
        }

        return Result.error(-23, "JWT Missing");
    }

    // ─────────────────────────────────────────────
    // /Course_student  —  学生选课管理
    // ─────────────────────────────────────────────

    /**
     * 获取学生的所有课程ID列表
     * 前端发: { first: studentId, second: jwt }
     * 返回: "\t\r" 分隔的 courseId 列表，或 "NULL"
     */
    @PostMapping("/Course_student/get_course_id_by_student")
    public Result<String> getCourseIdByStudent(@RequestBody Map<String, String> body,
                                               HttpServletRequest request) {
        String studentId = getParam(body, "first");
        String jwt = resolveJwt(body, request);

        Result<Void> auth = userService.checkJwt(0, studentId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        List<StudentCourse> list = studentCourseMapper.selectList(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId));

        if (list.isEmpty()) return Result.success("NULL");

        String ids = list.stream()
                .map(StudentCourse::getCourseId)
                .collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    /**
     * 学生通过课程码加入课程
     * 前端发: { first: studentId, second: jwt, third: courseCode }
     */
    @PostMapping("/Course_student/add_course")
    public Result<Void> addCourse(@RequestBody Map<String, String> body,
                                  HttpServletRequest request) {
        String studentId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseCode = getParam(body, "third");

        Result<Void> auth = userService.checkJwt(0, studentId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        // 通过课程码找课程
        Course course = courseMapper.selectOne(
                new LambdaQueryWrapper<Course>().eq(Course::getCode, courseCode));
        if (course == null) return Result.error(-21, "Course not found");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return archivedCheck;

        // 检查是否已加入
        Long exists = studentCourseMapper.selectCount(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId)
                        .eq(StudentCourse::getCourseId, course.getId()));
        if (exists > 0) return Result.error(-21, "Already enrolled");

        StudentCourse sc = new StudentCourse();
        sc.setStudentId(studentId);
        sc.setCourseId(course.getId());
        sc.setJoinedTime(LocalDateTime.now());
        studentCourseMapper.insert(sc);
        return Result.success();
    }

    @PostMapping("/Course_student/import_students_by_teacher")
    public Result<Map<String, Object>> importStudentsByTeacher(@RequestBody Map<String, String> body,
                                                               HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");
        String rawStudentIds = getParam(body, "fourth");

        if (courseId == null) courseId = getParam(body, "course_id");
        if (rawStudentIds == null) rawStudentIds = getParam(body, "student_ids");
        if (teacherId == null || courseId == null || rawStudentIds == null) {
            return Result.error(-10, "Missing params");
        }

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        Set<String> studentIds = new LinkedHashSet<>();
        for (String token : rawStudentIds.split("[,;\\s\\t\\r\\n]+")) {
            if (token == null) continue;
            String id = token.trim();
            if (!id.isEmpty()) {
                studentIds.add(id);
            }
        }
        if (studentIds.isEmpty()) return Result.error(-10, "No student ids");

        List<String> added = new java.util.ArrayList<>();
        List<String> existed = new java.util.ArrayList<>();
        List<String> notFound = new java.util.ArrayList<>();

        for (String studentId : studentIds) {
            Student student = studentMapper.selectById(studentId);
            if (student == null) {
                notFound.add(studentId);
                continue;
            }

            Long exists = studentCourseMapper.selectCount(
                    new LambdaQueryWrapper<StudentCourse>()
                            .eq(StudentCourse::getStudentId, studentId)
                            .eq(StudentCourse::getCourseId, courseId));
            if (exists != null && exists > 0) {
                existed.add(studentId);
                continue;
            }

            StudentCourse sc = new StudentCourse();
            sc.setStudentId(studentId);
            sc.setCourseId(courseId);
            sc.setJoinedTime(LocalDateTime.now());
            studentCourseMapper.insert(sc);
            added.add(studentId);
        }

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("total", studentIds.size());
        summary.put("addedCount", added.size());
        summary.put("existingCount", existed.size());
        summary.put("notFoundCount", notFound.size());
        summary.put("addedIds", added);
        summary.put("existingIds", existed);
        summary.put("notFoundIds", notFound);
        return Result.success(summary);
    }

    // ─────────────────────────────────────────────
    // /Course  —  课程信息
    // ─────────────────────────────────────────────

    /**
     * 通过课程ID获取课程详情
     * 前端发: { first: courseId, second: jwt }
     * 返回: "教师id\t\r课程名\t\r课程描述\t\r课程码\t\r学期\t\r是否激活\t\r创建时间"
     */
    @PostMapping("/Course/get_info_by_course_id")
    public Result<String> getCourseInfoById(@RequestBody Map<String, String> body,
                                            HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String courseId = getParam(body, "first");
        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");

        String data = String.join("\t\r",
                nvl(course.getTeacherId()),
                nvl(course.getName()),
                nvl(course.getInfo()),
                nvl(course.getCode()),
                nvl(course.getSemester()),
                nvl(course.getIsActive()),
                course.getCreatedTime() != null ? course.getCreatedTime().toString() : "");
        return Result.success(data);
    }

    /**
     * 获取教师的所有课程ID列表
     * 前端发: { first: teacherId, second: jwt }
     */
    @PostMapping("/Course/get_course_id_by_teacher")
    public Result<String> getCourseIdByTeacher(@RequestBody Map<String, String> body,
                                               HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        List<Course> courses = courseMapper.selectList(
                new LambdaQueryWrapper<Course>().eq(Course::getTeacherId, teacherId));
        if (courses.isEmpty()) return Result.success("NULL");

        String ids = courses.stream().map(Course::getId).collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    /**
     * 新建课程
     * 前端发: { first: teacherId, second: jwt, third: name, fourth: info, fifth: code, sixth: semester }
     */
    @PostMapping("/Course/new_course")
    public Result<Void> newCourse(@RequestBody Map<String, String> body,
                                  HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = new Course();
        // Generate a simple course ID or UUID
        String courseId = "C" + System.currentTimeMillis();
        course.setId(courseId);
        course.setTeacherId(teacherId);
        course.setName(getParam(body, "third"));
        course.setInfo(getParam(body, "fourth"));
        course.setCode(getParam(body, "fifth"));
        String semester = getParam(body, "sixth");
        course.setSemester(semester != null ? Integer.parseInt(semester) : 1);
        course.setIsActive(1);
        course.setCreatedTime(LocalDateTime.now());
        courseMapper.insert(course);
        return Result.success();
    }

    @PostMapping("/Course/delete_course")
    public Result<Void> deleteCourse(@RequestBody Map<String, String> body,
                                     HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");
        if (courseId == null) {
            courseId = getParam(body, "first");
            teacherId = getParam(body, "second");
        }

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        courseMapper.deleteById(courseId);
        return Result.success();
    }

    @PostMapping("/Course/archive_course")
    public Result<Void> archiveCourse(@RequestBody Map<String, String> body,
                                      HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");

        if (courseId == null) return Result.error(-10, "Missing course id");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        course.setIsActive(2);
        courseMapper.updateById(course);
        return Result.success();
    }

    @PostMapping("/Course/unarchive_course")
    public Result<Void> unarchiveCourse(@RequestBody Map<String, String> body,
                                        HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");

        if (courseId == null) return Result.error(-10, "Missing course id");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        course.setIsActive(1);
        courseMapper.updateById(course);
        return Result.success();
    }

    // ─────────────────────────────────────────────
    // /Course_student — 获取课程下的学生列表
    // ─────────────────────────────────────────────
    @PostMapping("/Course_student/get_student_id_by_course")
    public Result<String> getStudentIdByCourse(@RequestBody Map<String, String> body,
                                               HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        List<StudentCourse> list = studentCourseMapper.selectList(
                new LambdaQueryWrapper<StudentCourse>().eq(StudentCourse::getCourseId, courseId));
        if (list.isEmpty()) return Result.success("NULL");

        String ids = list.stream().map(StudentCourse::getStudentId).collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    // ─────────────────────────────────────────────
    // /Homework  —  作业管理
    // ─────────────────────────────────────────────

    /**
     * 获取课程的所有作业ID列表
     * 前端发: { first: capacity, second: userId, third: jwt, fourth: courseId }
     * 返回: "\t\r" 分隔的 homeworkId 列表，或 "NULL"
     */
    @PostMapping("/Homework/get_homework_id_by_course")
    public Result<String> getHomeworkIdByCourse(@RequestBody Map<String, String> body,
                                                HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String courseId = getParam(body, "fourth");
        if (courseId == null) {
            courseId = getParam(body, "first"); // some frontend parts use 'First' for courseId
        }
        List<Homework> list = homeworkMapper.selectList(
                new LambdaQueryWrapper<Homework>().eq(Homework::getCourseId, courseId));
        if (list.isEmpty()) return Result.success("NULL");

        String ids = list.stream()
                .map(h -> String.valueOf(h.getId()))
                .collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    /**
     * 通过作业ID获取作业详情
     * 前端发: { first: courseId, second: homeworkId }
     * 返回: "课程id\t\r标题\t\r描述\t\r截止日期\t\r创建时间"
     */
    @PostMapping("/Homework/get_info_by_homework_id")
    public Result<String> getHomeworkInfoById(@RequestBody Map<String, String> body,
                                              HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String homeworkIdStr = getParam(body, "second");
        if (homeworkIdStr == null) homeworkIdStr = getParam(body, "first");
        if (homeworkIdStr == null) return Result.error(-10, "Missing homework id");
        Homework hw = homeworkMapper.selectById(Integer.parseInt(homeworkIdStr.trim()));
        if (hw == null) return Result.error(-21, "Homework not found");

        String data = String.join("\t\r",
                nvl(hw.getTitle()),
                nvl(hw.getDescription()),
                hw.getDeadline() != null ? hw.getDeadline().toString() : "",
                hw.getCreateTime() != null ? hw.getCreateTime().toString() : "");
        return Result.success(data);
    }

    /**
     * 获取学生在某作业下的提交ID列表
     * 前端发: { first: capacity, second: userId, third: jwt, fourth: homeworkId, fifth: studentId }
     */
    @PostMapping("/Homework/get_submit_id_by_student")
    public Result<String> getSubmitIdByStudent(@RequestBody Map<String, String> body,
                                               HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String homeworkIdStr = getParam(body, "fourth");
        String studentId = getParam(body, "fifth");
        if (homeworkIdStr == null || studentId == null) return Result.error(-10, "Missing params");

        List<Submit> list = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>()
                        .eq(Submit::getHomeworkId, Integer.parseInt(homeworkIdStr.trim()))
                        .eq(Submit::getStudentId, studentId));
        if (list.isEmpty()) return Result.success("NULL");

        String ids = list.stream()
                .map(s -> String.valueOf(s.getId()))
                .collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    /**
     * 获取提交详情
     * 前端发: { first: capacity, second: userId, third: jwt, fourth: submitId }
     * 返回: "content_url\t\rscore\t\rai_feedback\t\rteacher_feedback\t\rcreate_time"
     */
    @PostMapping("/Homework/get_submit_info")
    public Result<String> getSubmitInfo(@RequestBody Map<String, String> body,
                                        HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String submitIdStr = getParam(body, "fourth");
        if (submitIdStr == null) submitIdStr = getParam(body, "first");
        if (submitIdStr == null) return Result.error(-10, "Missing submit id");

        Submit submit = submitMapper.selectById(Integer.parseInt(submitIdStr.trim()));
        if (submit == null) return Result.error(-21, "Submit not found");

        String data = String.join("\t\r",
                nvl(submit.getVideoUrl()),
                submit.getScore() != null ? submit.getScore().toString() : "",
                nvl(submit.getAiFeedback()),
                nvl(submit.getTeacherFeedback()),
                submit.getCreateTime() != null ? submit.getCreateTime().toString() : "");
        return Result.success(data);
    }

    /**
     * 更新AI评价
     * 前端发: { first: submitId, second: videoUrl, third: score, fourth: aiFeedback }
     */
    @PostMapping("/Homework/AI_test")
    public Result<Void> aiTest(@RequestBody Map<String, String> body,
                               HttpServletRequest request) {
        String teacherId = getParam(body, "teacher_id");
        String jwt = resolveJwt(body, request);
        String submitIdStr = getParam(body, "submit_id");
        String scoreStr = getParam(body, "score");
        String aiFeedback = getParam(body, "ai_feedback");

        // Legacy positional fallback: { first: teacherId, second: jwt, third: submitId, fourth: score, fifth: aiFeedback }
        if (submitIdStr == null) {
            teacherId = getParam(body, "first");
            if (jwt == null) jwt = getParam(body, "second");
            submitIdStr = getParam(body, "third");
            scoreStr = getParam(body, "fourth");
            aiFeedback = getParam(body, "fifth");
        }
        if (teacherId == null || submitIdStr == null) return Result.error(-10, "Missing params");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Submit submit = submitMapper.selectById(Integer.parseInt(submitIdStr.trim()));
        if (submit == null) return Result.error(-21, "Submit not found");
        Homework homework = homeworkMapper.selectById(submit.getHomeworkId());
        if (homework == null) return Result.error(-21, "Homework not found");
        Course course = courseMapper.selectById(homework.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        if (scoreStr != null && !scoreStr.isEmpty()) {
            try { submit.setScore(Integer.parseInt(scoreStr.trim())); } catch (NumberFormatException ignored) {}
        }
        if (aiFeedback != null) submit.setAiFeedback(aiFeedback);
        submitMapper.updateById(submit);
        return Result.success();
    }

    @PostMapping("/Homework/submit_homework")
    public Result<Integer> submitHomework(@RequestBody Map<String, String> body,
                                          HttpServletRequest request) {
        String studentId = getParam(body, "student_id");
        if (studentId == null) studentId = getParam(body, "first");
        String jwt = resolveJwt(body, request);

        String courseId = getParam(body, "course_id");
        if (courseId == null) courseId = getParam(body, "third");
        String homeworkIdStr = getParam(body, "homework_id");
        if (homeworkIdStr == null) homeworkIdStr = getParam(body, "fourth");
        if (homeworkIdStr == null) homeworkIdStr = getParam(body, "third");
        String videoUrl = getParam(body, "video_url");
        if (videoUrl == null) videoUrl = getParam(body, "fifth");
        if (videoUrl == null) videoUrl = getParam(body, "fourth");
        if (studentId == null || homeworkIdStr == null) return Result.error(-10, "Missing params");

        Result<Void> auth = userService.checkJwt(0, studentId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Homework homework = homeworkMapper.selectById(Integer.parseInt(homeworkIdStr.trim()));
        if (homework == null) return Result.error(-21, "Homework not found");
        if (courseId != null && !courseId.equals(homework.getCourseId())) return Result.error(-10, "Course/Homework mismatch");
        Course course = courseMapper.selectById(homework.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        Long enrolled = studentCourseMapper.selectCount(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId)
                        .eq(StudentCourse::getCourseId, homework.getCourseId()));
        if (enrolled == 0) return Result.error(-23, "JWT Error");

        Submit submit = new Submit();
        submit.setStudentId(studentId);
        submit.setHomeworkId(homework.getId());
        submit.setVideoUrl(videoUrl);
        submit.setCreateTime(LocalDateTime.now());
        submitMapper.insert(submit);
        return Result.success(submit.getId());
    }

    @PostMapping("/Homework/get_final_score")
    public Result<Integer> getFinalScore(@RequestBody Map<String, String> body,
                                         HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String studentId = getParam(body, "fourth");
        String homeworkIdStr = getParam(body, "fifth");
        if (homeworkIdStr == null) {
            homeworkIdStr = getParam(body, "second"); // In Teacher calls, might be different
        }
        
        List<Submit> submits = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>()
                        .eq(Submit::getHomeworkId, Integer.parseInt(homeworkIdStr.trim()))
                        .eq(studentId != null, Submit::getStudentId, studentId)
                        .orderByDesc(Submit::getCreateTime));
        
        if (submits.isEmpty() || submits.get(0).getScore() == null) {
            return Result.success(-26); // Magic number for 'no graded submission'
        }
        return Result.success(submits.get(0).getScore());
    }

    @PostMapping("/Homework/get_final_submit")
    public Result<String> getFinalSubmit(@RequestBody Map<String, String> body,
                                         HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");
        String hwIdStr = getParam(body, "fourth");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        List<StudentCourse> enrollments = studentCourseMapper.selectList(
                new LambdaQueryWrapper<StudentCourse>().eq(StudentCourse::getCourseId, courseId));

        if (enrollments.isEmpty()) return Result.success("NULL");

        StringBuilder result = new StringBuilder();
        for (StudentCourse sc : enrollments) {
            List<Submit> submits = submitMapper.selectList(
                    new LambdaQueryWrapper<Submit>()
                            .eq(Submit::getHomeworkId, Integer.parseInt(hwIdStr.trim()))
                            .eq(Submit::getStudentId, sc.getStudentId())
                            .orderByDesc(Submit::getCreateTime));

            if (!submits.isEmpty()) {
                if (result.length() > 0) result.append("\t\r");
                result.append(sc.getStudentId()).append("\n").append(submits.get(0).getId());
            }
        }

        return result.length() == 0 ? Result.success("NULL") : Result.success(result.toString());
    }

    @PostMapping("/Homework/new_homework")
    public Result<String> newHomework(@RequestBody Map<String, String> body,
                                      HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");
        if (courseId == null) {
            courseId = getParam(body, "first");
            teacherId = getParam(body, "second");
        }

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        Homework hw = new Homework();
        hw.setCourseId(courseId);
        hw.setTitle(getParam(body, "second"));
        String deadlineStr = getParam(body, "third");
        if (courseId != null && courseId.equals(deadlineStr)) {
            deadlineStr = getParam(body, "fourth");
        }
        hw.setDeadline(LocalDateTime.parse(deadlineStr.replace("Z", "")));
        hw.setDescription(getParam(body, "fourth"));
        if (deadlineStr != null && deadlineStr.equals(hw.getDescription())) {
            hw.setDescription(getParam(body, "fifth"));
        }
        hw.setCreateTime(LocalDateTime.now());
        homeworkMapper.insert(hw);
        return Result.success(String.valueOf(hw.getId()));
    }

    @PostMapping("/Homework/set_AI_type")
    public Result<Void> setAiType(@RequestBody Map<String, String> body,
                                  HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String hwIdStr = getParam(body, "third");
        String type = getParam(body, "fourth");
        String num = getParam(body, "fifth");
        if (num == null) {
            hwIdStr = getParam(body, "first");
            type = getParam(body, "second");
            num = getParam(body, "third");
            Homework hw = homeworkMapper.selectById(Integer.parseInt(hwIdStr.trim()));
            if (hw == null) return Result.error(-21, "Homework not found");
            Course course = courseMapper.selectById(hw.getCourseId());
            if (course == null) return Result.error(-21, "Course not found");
            teacherId = course.getTeacherId();
        }

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Homework hw = homeworkMapper.selectById(Integer.parseInt(hwIdStr.trim()));
        if (hw == null) return Result.error(-21, "Homework not found");
        Course course = courseMapper.selectById(hw.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        AiType ai = new AiType();
        ai.setHomeworkId(Integer.parseInt(hwIdStr.trim()));
        ai.setType(type);
        ai.setNum(Integer.parseInt(num.trim()));
        aiTypeMapper.insert(ai);
        return Result.success();
    }

    @PostMapping("/Homework/get_AI_type")
    public Result<String> getAiType(@RequestBody Map<String, String> body) {
        String hwIdStr = getParam(body, "first");
        AiType ai = aiTypeMapper.selectById(Integer.parseInt(hwIdStr.trim()));
        if (ai == null) return Result.success("squat\t\r10");
        return Result.success(ai.getType() + "\t\r" + ai.getNum());
    }

    @PostMapping("/Homework/edit_AI_type")
    public Result<Void> editAiType(@RequestBody Map<String, String> body,
                                   HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String hwIdStr = getParam(body, "third");
        String type = getParam(body, "fourth");
        String num = getParam(body, "fifth");
        if (num == null) {
            hwIdStr = getParam(body, "first");
            type = getParam(body, "second");
            num = getParam(body, "third");
            Homework hw = homeworkMapper.selectById(Integer.parseInt(hwIdStr.trim()));
            if (hw == null) return Result.error(-21, "Homework not found");
            Course course = courseMapper.selectById(hw.getCourseId());
            if (course == null) return Result.error(-21, "Course not found");
            teacherId = course.getTeacherId();
        }

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Homework hw = homeworkMapper.selectById(Integer.parseInt(hwIdStr.trim()));
        if (hw == null) return Result.error(-21, "Homework not found");
        Course course = courseMapper.selectById(hw.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        AiType ai = aiTypeMapper.selectById(Integer.parseInt(hwIdStr.trim()));
        if (ai != null) {
            ai.setType(type);
            ai.setNum(Integer.parseInt(num.trim()));
            aiTypeMapper.updateById(ai);
        }
        return Result.success();
    }

    @PostMapping("/Homework/get_submit_id_by_AI_not_test")
    public Result<String> getSubmitIdByAINotTest(@RequestBody Map<String, String> body,
                                                 HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String hwIdStr = getParam(body, "first");
        List<Submit> list = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>()
                        .eq(Submit::getHomeworkId, Integer.parseInt(hwIdStr.trim()))
                        .isNull(Submit::getAiFeedback));
        if (list.isEmpty()) return Result.success("NULL");
        String ids = list.stream().map(s -> String.valueOf(s.getId())).collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    @PostMapping("/Homework/get_submit_id_by_teacher_not_test")
    public Result<String> getSubmitIdByTeacherNotTest(@RequestBody Map<String, String> body,
                                                      HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String hwIdStr = getParam(body, "first");
        List<Submit> list = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>()
                        .eq(Submit::getHomeworkId, Integer.parseInt(hwIdStr.trim()))
                        .isNotNull(Submit::getAiFeedback)
                        .isNull(Submit::getTeacherFeedback));
        if (list.isEmpty()) return Result.success("NULL");
        String ids = list.stream().map(s -> String.valueOf(s.getId())).collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    @PostMapping("/Homework/edit_homework")
    public Result<Void> editHomework(@RequestBody Map<String, String> body,
                                     HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String hwIdStr = getParam(body, "fourth");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Homework hw = homeworkMapper.selectById(Integer.parseInt(hwIdStr.trim()));
        if (hw != null) {
            Course course = courseMapper.selectById(hw.getCourseId());
            if (course == null) return Result.error(-21, "Course not found");
            if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
            Result<Void> archivedCheck = rejectIfCourseArchived(course);
            if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());
            hw.setTitle(getParam(body, "fifth"));
            hw.setDescription(getParam(body, "sixth"));
            String deadlineStr = getParam(body, "seventh");
            if (deadlineStr != null && !deadlineStr.isEmpty()) {
                hw.setDeadline(LocalDateTime.parse(deadlineStr.replace("Z", "")));
            }
            homeworkMapper.updateById(hw);
        }
        return Result.success();
    }

    @PostMapping("/Homework/delete_homework")
    public Result<Void> deleteHomework(@RequestBody Map<String, String> body,
                                       HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String hwIdStr = getParam(body, "fourth");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Homework hw = homeworkMapper.selectById(Integer.parseInt(hwIdStr.trim()));
        if (hw == null) return Result.error(-21, "Homework not found");
        Course course = courseMapper.selectById(hw.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        homeworkMapper.deleteById(Integer.parseInt(hwIdStr.trim()));
        return Result.success();
    }

    @PostMapping("/Homework/get_submit_id_by_homework")
    public Result<String> getSubmitIdByHomework(@RequestBody Map<String, String> body,
                                                HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        String hwIdStr = getParam(body, "fourth");
        List<Submit> list = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>()
                        .eq(Submit::getHomeworkId, Integer.parseInt(hwIdStr.trim())));
        if (list.isEmpty()) return Result.success("NULL");
        String ids = list.stream().map(s -> String.valueOf(s.getId())).collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    @PostMapping("/Course_student/exit_course_by_student")
    public Result<Void> exitCourseByStudent(@RequestBody Map<String, String> body,
                                            HttpServletRequest request) {
        String studentId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");

        Result<Void> auth = userService.checkJwt(0, studentId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        studentCourseMapper.delete(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId)
                        .eq(StudentCourse::getCourseId, courseId));
        return Result.success();
    }

    @PostMapping("/Course_student/exit_course_by_teacher")
    public Result<Void> exitCourseByTeacher(@RequestBody Map<String, String> body,
                                            HttpServletRequest request) {
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");
        String studentId = getParam(body, "fourth");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        studentCourseMapper.delete(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId)
                        .eq(StudentCourse::getCourseId, courseId));
        return Result.success();
    }

    // ─────────────────────────────────────────────
    // /Class  —  教学视频管理
    // ─────────────────────────────────────────────

    @PostMapping("/Class/get_class_id_by_course")
    public Result<String> getClassIdByCourse(@RequestBody Map<String, String> body,
                                             HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        // Frontend sends: { first: capacity, second: teacherId, third: jwt, fourth: courseId }
        // or sometimes: { first: courseId }
        String courseId = getParam(body, "fourth");
        // If fourth is empty or just a single digit (like '1' for capacity), try first
        if (courseId == null || courseId.length() <= 1) {
            courseId = getParam(body, "first");
        }
        
        if (courseId == null) return Result.error(-10, "Missing course id");

        List<CourseClass> list = courseClassMapper.selectList(
                new LambdaQueryWrapper<CourseClass>().eq(CourseClass::getCourseId, courseId));
        if (list.isEmpty()) return Result.success("NULL");

        String ids = list.stream().map(c -> String.valueOf(c.getId())).collect(Collectors.joining("\t\r"));
        return Result.success(ids);
    }

    @PostMapping("/Class/get_info_by_class_id")
    public Result<String> getClassInfoById(@RequestBody Map<String, String> body,
                                           HttpServletRequest request) {
        Result<Void> auth = checkLegacyAuth(body, request);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        // Try second first, as it's often the classId in (courseId, classId) pairs
        String classIdStr = getParam(body, "second");
        
        // If second is not a number or missing, try first
        if (classIdStr == null || !isNumeric(classIdStr)) {
            classIdStr = getParam(body, "first");
        }
        
        if (classIdStr == null || !isNumeric(classIdStr)) {
            return Result.error(-10, "Missing or invalid class id: " + classIdStr);
        }

        try {
            CourseClass c = courseClassMapper.selectById(Integer.parseInt(classIdStr.trim()));
            if (c == null) return Result.error(-21, "Class not found");

            String data = String.join("\t\r",
                    nvl(c.getTitle()),
                    nvl(c.getDescription()),
                    nvl(c.getContentUrl()),
                    c.getCreateTime() != null ? c.getCreateTime().toString() : "");
            return Result.success(data);
        } catch (NumberFormatException e) {
            return Result.error(-10, "Invalid class id format: " + classIdStr);
        }
    }

    @PostMapping("/Class/new_class")
    public Result<Void> newClass(@RequestBody Map<String, String> body,
                                 HttpServletRequest request) {
        // Frontend sends: { first: teacherId, second: jwt, third: courseId, fourth: title, fifth: description, sixth: url }
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String courseId = getParam(body, "third");
        if (courseId == null) courseId = getParam(body, "first");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        CourseClass c = new CourseClass();
        c.setCourseId(courseId);
        c.setTitle(getParam(body, "fourth"));
        if (c.getTitle() == null) c.setTitle(getParam(body, "second"));

        c.setContentUrl(getParam(body, "sixth"));
        if (c.getContentUrl() == null) c.setContentUrl(getParam(body, "third"));

        c.setDescription(getParam(body, "fifth"));
        if (c.getDescription() == null) c.setDescription(getParam(body, "fourth"));

        c.setCreateTime(LocalDateTime.now());
        courseClassMapper.insert(c);
        return Result.success();
    }

    @PostMapping("/Class/edit_class")
    public Result<Void> editClass(@RequestBody Map<String, String> body,
                                  HttpServletRequest request) {
        // Frontend sends: { first: teacherId, second: jwt, third: courseId, fourth: classId, fifth: title, sixth: description, seventh: url }
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String classIdStr = getParam(body, "fourth");
        if (classIdStr == null || classIdStr.length() > 10) { // classId is usually a small int string, teacherId/courseId are long
            classIdStr = getParam(body, "first");
        }

        if (classIdStr == null) return Result.error(-10, "Missing class id");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        CourseClass c = courseClassMapper.selectById(Integer.parseInt(classIdStr.trim()));
        if (c != null) {
            Course course = courseMapper.selectById(c.getCourseId());
            if (course == null) return Result.error(-21, "Course not found");
            if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
            Result<Void> archivedCheck = rejectIfCourseArchived(course);
            if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());
            c.setTitle(getParam(body, "fifth"));
            if (c.getTitle() == null) c.setTitle(getParam(body, "second"));

            c.setContentUrl(getParam(body, "seventh"));
            if (c.getContentUrl() == null) c.setContentUrl(getParam(body, "third"));

            c.setDescription(getParam(body, "sixth"));
            if (c.getDescription() == null) c.setDescription(getParam(body, "fourth"));

            courseClassMapper.updateById(c);
        }
        return Result.success();
    }

    @PostMapping("/Class/delete_class")
    public Result<Void> deleteClass(@RequestBody Map<String, String> body,
                                    HttpServletRequest request) {
        // Frontend sends: { first: teacherId, second: jwt, third: courseId, fourth: classId }
        String teacherId = getParam(body, "first");
        String jwt = resolveJwt(body, request);
        String classIdStr = getParam(body, "fourth");
        if (classIdStr == null || classIdStr.length() > 10) {
            classIdStr = getParam(body, "first");
        }

        if (classIdStr == null) return Result.error(-10, "Missing class id");

        Result<Void> auth = userService.checkJwt(1, teacherId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        CourseClass courseClass = courseClassMapper.selectById(Integer.parseInt(classIdStr.trim()));
        if (courseClass == null) return Result.error(-21, "Class not found");
        Course course = courseMapper.selectById(courseClass.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        Result<Void> archivedCheck = rejectIfCourseArchived(course);
        if (archivedCheck != null) return Result.error(archivedCheck.getCode(), archivedCheck.getMessage());

        courseClassMapper.deleteById(Integer.parseInt(classIdStr.trim()));
        return Result.success();
    }

    // ─────────────────────────────────────────────
    // Helper
    // ─────────────────────────────────────────────
    private String nvl(Object o) {
        return o == null ? "" : o.toString();
    }

    private boolean isNumeric(String s) {
        if (s == null || s.trim().isEmpty()) return false;
        return s.trim().matches("\\d+");
    }
}
