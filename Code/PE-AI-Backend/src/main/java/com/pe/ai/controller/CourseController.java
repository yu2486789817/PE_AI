package com.pe.ai.controller;

import com.pe.ai.common.Result;
import com.pe.ai.entity.Course;
import com.pe.ai.entity.Homework;
import com.pe.ai.entity.Submit;
import com.pe.ai.service.CourseService;
import com.pe.ai.util.RequestValueResolver;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@SuppressWarnings("unchecked")

@RestController
@RequestMapping("/api/course")
@RequiredArgsConstructor
public class CourseController {

    private final CourseService courseService;

    private String getString(Map<String, Object> body, String key) {
        Object value = body == null ? null : body.get(key);
        return value == null ? null : value.toString();
    }

    private Integer getInteger(Map<String, Object> body, String key) {
        Object value = body == null ? null : body.get(key);
        if (value == null) {
            return null;
        }
        if (value instanceof Integer integer) {
            return integer;
        }
        return Integer.parseInt(value.toString());
    }

    private String resolveJwtFromQueryOrHeader(String jwt, HttpServletRequest request) {
        String normalized = RequestValueResolver.normalizeBearerToken(jwt);
        if (normalized != null) {
            return normalized;
        }
        return RequestValueResolver.resolveJwt(null, request);
    }

    @GetMapping("/teacher/{teacherId}")
    public Result<List<Course>> getCoursesByTeacher(@PathVariable String teacherId,
                                                    @RequestParam(required = false) String jwt,
                                                    HttpServletRequest request) {
        return courseService.getCoursesByTeacher(teacherId, resolveJwtFromQueryOrHeader(jwt, request));
    }

    @GetMapping("/{courseId}")
    public Result<Course> getCourse(@PathVariable String courseId,
                                    @RequestParam String teacherId,
                                    @RequestParam(required = false) String jwt,
                                    HttpServletRequest request) {
        return courseService.getCourseById(courseId, teacherId, resolveJwtFromQueryOrHeader(jwt, request));
    }

    @PostMapping("/create")
    public Result<Void> createCourse(@RequestBody Map<String, Object> body,
                                     HttpServletRequest request) {
        return courseService.createCourse(
                getString(body, "id"),
                getString(body, "teacher_id"),
                getString(body, "name"),
                getString(body, "info"),
                getString(body, "code"),
                getInteger(body, "semester"),
                RequestValueResolver.resolveJwt((Map) body, request));
    }

    @PutMapping("/update")
    public Result<Void> updateCourse(@RequestBody Map<String, Object> body,
                                     HttpServletRequest request) {
        return courseService.updateCourse(
                getString(body, "id"),
                getString(body, "teacher_id"),
                getString(body, "name"),
                getString(body, "info"),
                getInteger(body, "is_active"),
                RequestValueResolver.resolveJwt((Map) body, request));
    }

    // ==================== HOMEWORK ====================

    @GetMapping("/{courseId}/homework")
    public Result<List<Homework>> getHomeworks(@PathVariable String courseId,
                                               @RequestParam String teacherId,
                                               @RequestParam(required = false) String jwt,
                                               HttpServletRequest request) {
        return courseService.getHomeworksByCourse(courseId, teacherId, resolveJwtFromQueryOrHeader(jwt, request));
    }

    @PostMapping("/homework/create")
    public Result<Void> createHomework(@RequestBody Map<String, Object> body,
                                       HttpServletRequest request) {
        return courseService.createHomework(
                getString(body, "course_id"),
                getString(body, "teacher_id"),
                getString(body, "title"),
                getString(body, "description"),
                LocalDateTime.parse(getString(body, "deadline")),
                RequestValueResolver.resolveJwt((Map) body, request));
    }

    // ==================== SUBMIT ====================

    @GetMapping("/homework/{homeworkId}/submit")
    public Result<List<Submit>> getSubmits(@PathVariable Integer homeworkId,
                                           @RequestParam String teacherId,
                                           @RequestParam(required = false) String jwt,
                                           HttpServletRequest request) {
        return courseService.getSubmitsByHomework(homeworkId, teacherId, resolveJwtFromQueryOrHeader(jwt, request));
    }

    @PostMapping("/submit/create")
    public Result<Void> createSubmit(@RequestBody Map<String, Object> body,
                                     HttpServletRequest request) {
        return courseService.createSubmit(
                getInteger(body, "homework_id"),
                getString(body, "student_id"),
                getString(body, "video_url"),
                RequestValueResolver.resolveJwt((Map) body, request));
    }

    @PutMapping("/submit/score")
    public Result<Void> scoreSubmit(@RequestBody Map<String, Object> body,
                                    HttpServletRequest request) {
        return courseService.scoreSubmit(
                getInteger(body, "id"),
                getString(body, "teacher_id"),
                getInteger(body, "score"),
                getString(body, "teacher_feedback"),
                RequestValueResolver.resolveJwt((Map) body, request));
    }
}
