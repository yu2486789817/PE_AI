package com.pe.ai.service;

import com.pe.ai.common.Result;
import com.pe.ai.entity.Student;
import com.pe.ai.entity.StdStudent;
import com.pe.ai.entity.StdTeacher;
import com.pe.ai.entity.Teacher;
import com.pe.ai.mapper.StdStudentMapper;
import com.pe.ai.mapper.StdTeacherMapper;
import com.pe.ai.mapper.StudentMapper;
import com.pe.ai.mapper.TeacherMapper;
import com.pe.ai.util.RequestValueResolver;
import com.pe.ai.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class UserService {

    private final TeacherMapper teacherMapper;
    private final StudentMapper studentMapper;
    private final StdStudentMapper stdStudentMapper;
    private final StdTeacherMapper stdTeacherMapper;

    // ==================== LOGIN ====================

    public Result<String> teacherLogin(String id, String password) {
        Teacher teacher = teacherMapper.selectById(id);
        if (teacher == null) {
            return Result.error(-21, "User not found");
        }
        if (!teacher.getPassword().equals(password)) {
            return Result.error(-23, "Wrong password");
        }
        // Update login time
        teacher.setLoginTime(LocalDateTime.now());
        teacherMapper.updateById(teacher);

        String token = SecurityUtil.generateToken(id, teacher.getPassword());
        return Result.success(token);
    }

    public Result<String> studentLogin(String id, String password) {
        Student student = studentMapper.selectById(id);
        if (student == null) {
            return Result.error(-21, "User not found");
        }
        if (!student.getPassword().equals(password)) {
            return Result.error(-23, "Wrong password");
        }
        student.setLoginTime(LocalDateTime.now());
        studentMapper.updateById(student);

        String token = SecurityUtil.generateToken(id, student.getPassword());
        return Result.success(token);
    }

    // ==================== JWT CHECK ====================

    public Result<Void> checkJwt(int capacity, String id, String jwt) {
        String normalizedJwt = normalizeJwt(jwt);
        if (capacity == 0) {
            return checkStudentJwt(id, normalizedJwt);
        } else if (capacity == 1) {
            return checkTeacherJwt(id, normalizedJwt);
        }
        return Result.error(-2, "Error Capacity");
    }

    private Result<Void> checkStudentJwt(String id, String jwt) {
        Student student = studentMapper.selectById(id);
        if (student == null) {
            return Result.error(-21, "User not found");
        }
        if (jwt == null || jwt.length() < 14) {
            return Result.error(-23, "JWT Missing");
        }
        if (!SecurityUtil.validateToken(jwt, id, student.getPassword())) {
            String jwtTime = jwt.substring(0, 14);
            if (SecurityUtil.isTokenExpired(jwtTime)) {
                return Result.error(-24, "JWT TLE");
            }
            return Result.error(-23, "JWT Error");
        }
        return Result.success();
    }

    private Result<Void> checkTeacherJwt(String id, String jwt) {
        Teacher teacher = teacherMapper.selectById(id);
        if (teacher == null) {
            return Result.error(-21, "User not found");
        }
        if (jwt == null || jwt.length() < 14) {
            return Result.error(-23, "JWT Missing");
        }
        if (!SecurityUtil.validateToken(jwt, id, teacher.getPassword())) {
            String jwtTime = jwt.substring(0, 14);
            if (SecurityUtil.isTokenExpired(jwtTime)) {
                return Result.error(-24, "JWT TLE");
            }
            return Result.error(-23, "JWT Error");
        }
        return Result.success();
    }

    private String normalizeJwt(String jwt) {
        return RequestValueResolver.normalizeBearerToken(jwt);
    }

    // ==================== REGISTER ====================

    public Result<Void> registerTeacher(String id, String password, String name,
                                         String gender, String title, String college, String department) {
        // Check if already registered
        if (teacherMapper.selectById(id) != null) {
            return Result.error(-21, "User Collide");
        }
        // Check if ID exists in std_teacher baseline table (original logic)
        if (stdTeacherMapper.selectById(id) == null) {
            return Result.error(-22, "User not found in baseline");
        }

        Teacher teacher = new Teacher();
        teacher.setId(id);
        teacher.setPassword(password);
        teacher.setName(name);
        teacher.setGender(gender);
        teacher.setTitle(title);
        teacher.setCollege(college);
        teacher.setDepartment(department);
        teacher.setCreatedTime(LocalDateTime.now());
        teacherMapper.insert(teacher);
        return Result.success();
    }

    public Result<Void> registerStudent(String id, String password, String name,
                                         String gender, String major, String college, String department) {
        // Check if already registered
        if (studentMapper.selectById(id) != null) {
            return Result.error(-21, "User Collide");
        }
        // Check if ID exists in std_student baseline table (original logic)
        if (stdStudentMapper.selectById(id) == null) {
            return Result.error(-22, "User not found in baseline");
        }

        Student student = new Student();
        student.setId(id);
        student.setPassword(password);
        student.setName(name);
        student.setGender(gender);
        student.setMajor(major);
        student.setCollege(college);
        student.setDepartment(department);
        student.setCreatedTime(LocalDateTime.now());
        studentMapper.insert(student);
        return Result.success();
    }

    // ==================== CHANGE PASSWORD ====================

    public Result<Void> changeTeacherPassword(String id, String jwt, String oldPassword, String newPassword) {
        Result<Void> authResult = checkJwt(1, id, jwt);
        if (authResult.getCode() < 0) return authResult;

        Teacher teacher = teacherMapper.selectById(id);
        if (teacher == null) return Result.error(-21, "User not found");
        if (!teacher.getPassword().equals(oldPassword)) return Result.error(-23, "Old Password Error");

        teacher.setPassword(newPassword);
        teacherMapper.updateById(teacher);
        return Result.success();
    }

    public Result<Void> changeStudentPassword(String id, String jwt, String oldPassword, String newPassword) {
        Result<Void> authResult = checkJwt(0, id, jwt);
        if (authResult.getCode() < 0) return authResult;

        Student student = studentMapper.selectById(id);
        if (student == null) return Result.error(-21, "User not found");
        if (!student.getPassword().equals(oldPassword)) return Result.error(-23, "Old Password Error");

        student.setPassword(newPassword);
        studentMapper.updateById(student);
        return Result.success();
    }

    // ==================== GET INFO ====================

    public Result<Teacher> getTeacherInfo(String teacherId) {
        Teacher teacher = teacherMapper.selectById(teacherId);
        if (teacher == null) return Result.error(-21, "User not found");
        teacher.setPassword(null); // Don't expose password
        return Result.success(teacher);
    }

    public Result<Student> getStudentInfo(String studentId) {
        Student student = studentMapper.selectById(studentId);
        if (student == null) return Result.error(-21, "User not found");
        student.setPassword(null);
        return Result.success(student);
    }
}
