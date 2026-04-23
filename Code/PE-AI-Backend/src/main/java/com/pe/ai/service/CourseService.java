package com.pe.ai.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pe.ai.common.Result;
import com.pe.ai.entity.Course;
import com.pe.ai.entity.Homework;
import com.pe.ai.entity.StudentCourse;
import com.pe.ai.entity.Submit;
import com.pe.ai.mapper.CourseMapper;
import com.pe.ai.mapper.HomeworkMapper;
import com.pe.ai.mapper.StudentCourseMapper;
import com.pe.ai.mapper.SubmitMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class CourseService {

    private final CourseMapper courseMapper;
    private final HomeworkMapper homeworkMapper;
    private final SubmitMapper submitMapper;
    private final StudentCourseMapper studentCourseMapper;
    private final UserService userService;

    // ==================== COURSE CRUD ====================

    public Result<List<Course>> getCoursesByTeacher(String teacherId, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return Result.error(authResult.getCode(), authResult.getMessage());

        List<Course> courses = courseMapper.selectList(
                new LambdaQueryWrapper<Course>().eq(Course::getTeacherId, teacherId));
        return Result.success(courses);
    }

    public Result<Course> getCourseById(String courseId, String teacherId, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return Result.error(authResult.getCode(), authResult.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        return Result.success(course);
    }

    public Result<Void> createCourse(String id, String teacherId, String name,
                                      String info, String code, Integer semester, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return authResult;

        Course course = new Course();
        course.setId(id);
        course.setTeacherId(teacherId);
        course.setName(name);
        course.setInfo(info);
        course.setCode(code);
        course.setSemester(semester);
        course.setIsActive(1);
        course.setCreatedTime(LocalDateTime.now());
        courseMapper.insert(course);
        return Result.success();
    }

    public Result<Void> updateCourse(String id, String teacherId, String name, String info, Integer isActive, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return authResult;

        Course course = courseMapper.selectById(id);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        if (name != null) course.setName(name);
        if (info != null) course.setInfo(info);
        if (isActive != null) course.setIsActive(isActive);
        courseMapper.updateById(course);
        return Result.success();
    }

    // ==================== HOMEWORK CRUD ====================

    public Result<List<Homework>> getHomeworksByCourse(String courseId, String teacherId, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return Result.error(authResult.getCode(), authResult.getMessage());

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        List<Homework> list = homeworkMapper.selectList(
                new LambdaQueryWrapper<Homework>().eq(Homework::getCourseId, courseId));
        return Result.success(list);
    }

    public Result<Void> createHomework(String courseId, String teacherId, String title, String description, LocalDateTime deadline, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return authResult;

        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        Homework hw = new Homework();
        hw.setCourseId(courseId);
        hw.setTitle(title);
        hw.setDescription(description);
        hw.setDeadline(deadline);
        hw.setCreateTime(LocalDateTime.now());
        homeworkMapper.insert(hw);
        return Result.success();
    }

    // ==================== SUBMIT CRUD ====================

    public Result<List<Submit>> getSubmitsByHomework(Integer homeworkId, String teacherId, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return Result.error(authResult.getCode(), authResult.getMessage());

        Homework homework = homeworkMapper.selectById(homeworkId);
        if (homework == null) return Result.error(-21, "Homework not found");
        Course course = courseMapper.selectById(homework.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");

        List<Submit> list = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>().eq(Submit::getHomeworkId, homeworkId));
        return Result.success(list);
    }

    public Result<Void> createSubmit(Integer homeworkId, String studentId, String videoUrl, String jwt) {
        Result<Void> authResult = userService.checkJwt(0, studentId, jwt);
        if (authResult.getCode() < 0) return authResult;

        Homework homework = homeworkMapper.selectById(homeworkId);
        if (homework == null) return Result.error(-21, "Homework not found");
        Long enrolled = studentCourseMapper.selectCount(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId)
                        .eq(StudentCourse::getCourseId, homework.getCourseId()));
        if (enrolled == 0) return Result.error(-23, "JWT Error");

        Submit submit = new Submit();
        submit.setHomeworkId(homeworkId);
        submit.setStudentId(studentId);
        submit.setVideoUrl(videoUrl);
        submit.setCreateTime(LocalDateTime.now());
        submitMapper.insert(submit);
        return Result.success();
    }

    public Result<Void> scoreSubmit(Integer submitId, String teacherId, Integer score, String teacherFeedback, String jwt) {
        Result<Void> authResult = userService.checkJwt(1, teacherId, jwt);
        if (authResult.getCode() < 0) return authResult;

        Submit submit = submitMapper.selectById(submitId);
        if (submit == null) return Result.error(-21, "Submit not found");
        Homework homework = homeworkMapper.selectById(submit.getHomeworkId());
        if (homework == null) return Result.error(-21, "Homework not found");
        Course course = courseMapper.selectById(homework.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (!teacherId.equals(course.getTeacherId())) return Result.error(-23, "JWT Error");
        submit.setScore(score);
        submit.setTeacherFeedback(teacherFeedback);
        submitMapper.updateById(submit);
        return Result.success();
    }
}
