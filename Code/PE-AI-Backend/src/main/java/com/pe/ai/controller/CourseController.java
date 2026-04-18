package com.pe.ai.controller;

import com.pe.ai.common.Result;
import com.pe.ai.entity.Course;
import com.pe.ai.entity.Homework;
import com.pe.ai.entity.Submit;
import com.pe.ai.service.CourseService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/course")
@RequiredArgsConstructor
public class CourseController {

    private final CourseService courseService;

    @GetMapping("/teacher/{teacherId}")
    public Result<List<Course>> getCoursesByTeacher(@PathVariable String teacherId) {
        return courseService.getCoursesByTeacher(teacherId);
    }

    @GetMapping("/{courseId}")
    public Result<Course> getCourse(@PathVariable String courseId) {
        return courseService.getCourseById(courseId);
    }

    @PostMapping("/create")
    public Result<Void> createCourse(@RequestBody Map<String, Object> body) {
        return courseService.createCourse(
                (String) body.get("id"),
                (String) body.get("teacher_id"),
                (String) body.get("name"),
                (String) body.get("info"),
                (String) body.get("code"),
                (Integer) body.get("semester"));
    }

    @PutMapping("/update")
    public Result<Void> updateCourse(@RequestBody Map<String, Object> body) {
        return courseService.updateCourse(
                (String) body.get("id"),
                (String) body.get("name"),
                (String) body.get("info"),
                (Integer) body.get("is_active"));
    }

    // ==================== HOMEWORK ====================

    @GetMapping("/{courseId}/homework")
    public Result<List<Homework>> getHomeworks(@PathVariable String courseId) {
        return courseService.getHomeworksByCourse(courseId);
    }

    @PostMapping("/homework/create")
    public Result<Void> createHomework(@RequestBody Map<String, Object> body) {
        return courseService.createHomework(
                (String) body.get("course_id"),
                (String) body.get("title"),
                (String) body.get("description"),
                LocalDateTime.parse((String) body.get("deadline")));
    }

    // ==================== SUBMIT ====================

    @GetMapping("/homework/{homeworkId}/submit")
    public Result<List<Submit>> getSubmits(@PathVariable Integer homeworkId) {
        return courseService.getSubmitsByHomework(homeworkId);
    }

    @PostMapping("/submit/create")
    public Result<Void> createSubmit(@RequestBody Map<String, Object> body) {
        return courseService.createSubmit(
                (Integer) body.get("homework_id"),
                (String) body.get("student_id"),
                (String) body.get("video_url"));
    }

    @PutMapping("/submit/score")
    public Result<Void> scoreSubmit(@RequestBody Map<String, Object> body) {
        return courseService.scoreSubmit(
                (Integer) body.get("id"),
                (Integer) body.get("score"),
                (String) body.get("teacher_feedback"));
    }
}
