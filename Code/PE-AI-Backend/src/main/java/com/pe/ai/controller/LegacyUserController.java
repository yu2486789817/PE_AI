package com.pe.ai.controller;

import com.pe.ai.common.Result;
import com.pe.ai.entity.Student;
import com.pe.ai.entity.Teacher;
import com.pe.ai.service.UserService;
import com.pe.ai.util.RequestValueResolver;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Legacy-compatible controller that matches the original .NET API paths and parameter format.
 * The old frontend sends parameters as: { "first": ..., "second": ..., "third": ... }
 * and calls paths like /User/login_teacher, /User/new_student, etc.
 *
 * This controller bridges the old frontend to the new Spring Boot backend.
 */
@RestController
@RequestMapping("/User")
@RequiredArgsConstructor
public class LegacyUserController {

    private final UserService userService;

    private String getParam(Map<String, String> body, String key) {
        return RequestValueResolver.getIgnoreCase(body, key);
    }

    private String resolveTargetId(Map<String, String> body, String explicitKey) {
        String id = getParam(body, explicitKey);
        if (id == null) id = getParam(body, "target_id");
        if (id == null) id = getParam(body, "fourth");
        if (id == null) id = getParam(body, "first");
        return id;
    }

    private Integer parseCapacity(String raw) {
        if (raw == null) {
            return null;
        }
        String value = raw.trim();
        if ("0".equals(value) || "student".equalsIgnoreCase(value)) {
            return 0;
        }
        if ("1".equals(value) || "teacher".equalsIgnoreCase(value)) {
            return 1;
        }
        return null;
    }

    private Result<Void> checkReadAuth(int targetCapacity, String targetId, Map<String, String> body,
                                       HttpServletRequest request) {
        Integer legacyCapacity = parseCapacity(getParam(body, "first"));
        String legacyRequesterId = getParam(body, "second");
        String legacyJwt = getParam(body, "third");
        if (legacyCapacity != null && legacyRequesterId != null && legacyJwt != null) {
            return userService.checkJwt(
                    legacyCapacity,
                    legacyRequesterId,
                    RequestValueResolver.normalizeBearerToken(legacyJwt));
        }

        String requesterId = getParam(body, "user_id");
        if (requesterId == null) requesterId = getParam(body, "first");

        Integer requesterCapacity = parseCapacity(getParam(body, "capacity"));
        if (requesterCapacity == null) requesterCapacity = parseCapacity(getParam(body, "user_type"));
        if (requesterCapacity == null) requesterCapacity = parseCapacity(getParam(body, "third"));

        String jwt = RequestValueResolver.resolveJwt(body, request);
        if (requesterCapacity != null && requesterId != null) {
            return userService.checkJwt(requesterCapacity, requesterId, jwt);
        }

        return userService.checkJwt(targetCapacity, targetId, jwt);
    }

    // ==================== LOGIN ====================

    @PostMapping("/login_teacher")
    public Result<String> loginTeacher(@RequestBody Map<String, String> body) {
        return userService.teacherLogin(getParam(body, "first"), getParam(body, "second"));
    }

    @PostMapping("/login_student")
    public Result<String> studentLogin(@RequestBody Map<String, String> body) {
        return userService.studentLogin(getParam(body, "first"), getParam(body, "second"));
    }

    // ==================== REGISTER ====================

    @PostMapping("/new_teacher")
    public Result<Void> newTeacher(@RequestBody Map<String, String> body) {
        return userService.registerTeacher(
                getParam(body, "first"),   // id
                getParam(body, "second"),  // password (SHA256 hash)
                getParam(body, "third"),   // name
                getParam(body, "fourth"),  // gender
                getParam(body, "fifth"),   // title
                getParam(body, "sixth"),   // college
                getParam(body, "seventh")  // department
        );
    }

    @PostMapping("/new_student")
    public Result<Void> newStudent(@RequestBody Map<String, String> body) {
        return userService.registerStudent(
                getParam(body, "first"),   // id
                getParam(body, "second"),  // password (SHA256 hash)
                getParam(body, "third"),   // name
                getParam(body, "fourth"),  // gender
                getParam(body, "fifth"),   // major
                getParam(body, "sixth"),   // college
                getParam(body, "seventh")  // department
        );
    }

    // ==================== CHANGE PASSWORD ====================

    @PostMapping("/change_teacher_password")
    public Result<Void> changeTeacherPassword(@RequestBody Map<String, String> body,
                                              HttpServletRequest request) {
        return userService.changeTeacherPassword(
                getParam(body, "first"),   // id
                RequestValueResolver.resolveJwt(body, request),
                getParam(body, "second"),  // old password
                getParam(body, "third")    // new password
        );
    }

    @PostMapping("/change_student_password")
    public Result<Void> changeStudentPassword(@RequestBody Map<String, String> body,
                                              HttpServletRequest request) {
        return userService.changeStudentPassword(
                getParam(body, "first"),   // id
                RequestValueResolver.resolveJwt(body, request),
                getParam(body, "second"),  // old password
                getParam(body, "third")    // new password
        );
    }

    // ==================== GET INFO ====================
    // The old frontend expects data returned as tab-separated string: "name\t\rgender\t\rtitle..."

    @PostMapping("/get_teacher_info")
    public Result<String> getTeacherInfo(@RequestBody Map<String, String> body,
                                         HttpServletRequest request) {
        String teacherId = resolveTargetId(body, "teacher_id");
        Result<Void> auth = checkReadAuth(1, teacherId, body, request);
        if (auth.getCode() < 0) {
            return Result.error(auth.getCode(), auth.getMessage());
        }
        Result<Teacher> result = userService.getTeacherInfo(teacherId);
        if (result.getCode() < 0) {
            return Result.error(result.getCode(), result.getMessage());
        }
        Teacher t = result.getData();
        // Return in legacy tab-separated format for frontend compatibility
        String data = String.join("\t\r",
                nvl(t.getName()), nvl(t.getGender()), nvl(t.getTitle()),
                nvl(t.getCollege()), nvl(t.getDepartment()));
        return Result.success(data);
    }

    @PostMapping("/get_student_info")
    public Result<String> getStudentInfo(@RequestBody Map<String, String> body,
                                         HttpServletRequest request) {
        String studentId = resolveTargetId(body, "student_id");
        Result<Void> auth = checkReadAuth(0, studentId, body, request);
        if (auth.getCode() < 0) {
            return Result.error(auth.getCode(), auth.getMessage());
        }
        Result<Student> result = userService.getStudentInfo(studentId);
        if (result.getCode() < 0) {
            return Result.error(result.getCode(), result.getMessage());
        }
        Student s = result.getData();
        String data = String.join("\t\r",
                nvl(s.getName()), nvl(s.getGender()), nvl(s.getMajor()),
                nvl(s.getCollege()), nvl(s.getDepartment()));
        return Result.success(data);
    }

    private String nvl(String s) {
        return s == null ? "" : s;
    }
}
