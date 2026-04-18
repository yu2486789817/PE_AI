package com.pe.ai.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pe.ai.common.Result;
import com.pe.ai.entity.Course;
import com.pe.ai.entity.Homework;
import com.pe.ai.entity.Submit;
import com.pe.ai.mapper.CourseMapper;
import com.pe.ai.mapper.HomeworkMapper;
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
    private final UserService userService;

    // ==================== COURSE CRUD ====================

    public Result<List<Course>> getCoursesByTeacher(String teacherId) {
        List<Course> courses = courseMapper.selectList(
                new LambdaQueryWrapper<Course>().eq(Course::getTeacherId, teacherId));
        return Result.success(courses);
    }

    public Result<Course> getCourseById(String courseId) {
        Course course = courseMapper.selectById(courseId);
        if (course == null) return Result.error(-21, "Course not found");
        return Result.success(course);
    }

    public Result<Void> createCourse(String id, String teacherId, String name,
                                      String info, String code, int semester) {
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

    public Result<Void> updateCourse(String id, String name, String info, Integer isActive) {
        Course course = courseMapper.selectById(id);
        if (course == null) return Result.error(-21, "Course not found");
        if (name != null) course.setName(name);
        if (info != null) course.setInfo(info);
        if (isActive != null) course.setIsActive(isActive);
        courseMapper.updateById(course);
        return Result.success();
    }

    // ==================== HOMEWORK CRUD ====================

    public Result<List<Homework>> getHomeworksByCourse(String courseId) {
        List<Homework> list = homeworkMapper.selectList(
                new LambdaQueryWrapper<Homework>().eq(Homework::getCourseId, courseId));
        return Result.success(list);
    }

    public Result<Void> createHomework(String courseId, String title, String description, LocalDateTime deadline) {
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

    public Result<List<Submit>> getSubmitsByHomework(Integer homeworkId) {
        List<Submit> list = submitMapper.selectList(
                new LambdaQueryWrapper<Submit>().eq(Submit::getHomeworkId, homeworkId));
        return Result.success(list);
    }

    public Result<Void> createSubmit(Integer homeworkId, String studentId, String videoUrl) {
        Submit submit = new Submit();
        submit.setHomeworkId(homeworkId);
        submit.setStudentId(studentId);
        submit.setVideoUrl(videoUrl);
        submit.setCreateTime(LocalDateTime.now());
        submitMapper.insert(submit);
        return Result.success();
    }

    public Result<Void> scoreSubmit(Integer submitId, Integer score, String teacherFeedback) {
        Submit submit = submitMapper.selectById(submitId);
        if (submit == null) return Result.error(-21, "Submit not found");
        submit.setScore(score);
        submit.setTeacherFeedback(teacherFeedback);
        submitMapper.updateById(submit);
        return Result.success();
    }
}
