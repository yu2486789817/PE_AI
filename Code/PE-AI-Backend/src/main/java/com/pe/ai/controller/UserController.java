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

@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    private String getParam(Map<String, String> body, String key) {
        return RequestValueResolver.getIgnoreCase(body, key);
    }

    // ==================== LOGIN ====================

    @PostMapping("/teacher/login")
    public Result<String> teacherLogin(@RequestBody Map<String, String> body) {
        return userService.teacherLogin(getParam(body, "id"), getParam(body, "password"));
    }

    @PostMapping("/student/login")
    public Result<String> studentLogin(@RequestBody Map<String, String> body) {
        return userService.studentLogin(getParam(body, "id"), getParam(body, "password"));
    }

    // ==================== CHECK JWT ====================

    @PostMapping("/checkjwt")
    public Result<Void> checkJwt(@RequestBody Map<String, String> body,
                                 HttpServletRequest request) {
        String capacityStr = getParam(body, "capacity");
        int capacity = Integer.parseInt(capacityStr == null ? "0" : capacityStr);
        return userService.checkJwt(capacity, getParam(body, "id"), RequestValueResolver.resolveJwt(body, request));
    }

    // ==================== REGISTER ====================

    @PostMapping("/teacher/register")
    public Result<Void> registerTeacher(@RequestBody Map<String, String> body) {
        return userService.registerTeacher(
                getParam(body, "id"), getParam(body, "password"), getParam(body, "name"),
                getParam(body, "gender"), getParam(body, "title"),
                getParam(body, "college"), getParam(body, "department"));
    }

    @PostMapping("/student/register")
    public Result<Void> registerStudent(@RequestBody Map<String, String> body) {
        return userService.registerStudent(
                getParam(body, "id"), getParam(body, "password"), getParam(body, "name"),
                getParam(body, "gender"), getParam(body, "major"),
                getParam(body, "college"), getParam(body, "department"));
    }

    // ==================== UPDATE INFO ====================

    @PostMapping("/teacher/update")
    public Result<Void> updateTeacherInfo(@RequestBody Map<String, String> body,
                                          HttpServletRequest request) {
        return userService.updateTeacherInfo(
                getParam(body, "id"), RequestValueResolver.resolveJwt(body, request), getParam(body, "name"),
                getParam(body, "gender"), getParam(body, "title"),
                getParam(body, "college"), getParam(body, "department"));
    }

    @PostMapping("/student/update")
    public Result<Void> updateStudentInfo(@RequestBody Map<String, String> body,
                                          HttpServletRequest request) {
        return userService.updateStudentInfo(
                getParam(body, "id"), RequestValueResolver.resolveJwt(body, request), getParam(body, "name"),
                getParam(body, "gender"), getParam(body, "major"),
                getParam(body, "college"), getParam(body, "department"));
    }

    // ==================== CHANGE PASSWORD ====================

    @PostMapping("/teacher/password")
    public Result<Void> changeTeacherPassword(@RequestBody Map<String, String> body,
                                              HttpServletRequest request) {
        return userService.changeTeacherPassword(
                getParam(body, "id"), RequestValueResolver.resolveJwt(body, request),
                getParam(body, "old_password"), getParam(body, "new_password"));
    }

    @PostMapping("/student/password")
    public Result<Void> changeStudentPassword(@RequestBody Map<String, String> body,
                                              HttpServletRequest request) {
        return userService.changeStudentPassword(
                getParam(body, "id"), RequestValueResolver.resolveJwt(body, request),
                getParam(body, "old_password"), getParam(body, "new_password"));
    }

    // ==================== GET INFO ====================

    @GetMapping("/teacher/info")
    public Result<Teacher> getTeacherInfo(@RequestParam String id,
                                          @RequestParam String jwt) {
        Result<Void> authResult = userService.checkJwt(1, id, RequestValueResolver.normalizeBearerToken(jwt));
        if (authResult.getCode() < 0) return Result.error(authResult.getCode(), authResult.getMessage());
        return userService.getTeacherInfo(id);
    }

    @GetMapping("/student/info")
    public Result<Student> getStudentInfo(@RequestParam String id,
                                          @RequestParam String jwt) {
        Result<Void> authResult = userService.checkJwt(0, id, RequestValueResolver.normalizeBearerToken(jwt));
        if (authResult.getCode() < 0) return Result.error(authResult.getCode(), authResult.getMessage());
        return userService.getStudentInfo(id);
    }
}
