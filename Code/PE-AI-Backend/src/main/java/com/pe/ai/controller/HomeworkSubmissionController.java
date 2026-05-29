package com.pe.ai.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.pe.ai.common.Result;
import com.pe.ai.entity.AiType;
import com.pe.ai.entity.Course;
import com.pe.ai.entity.Homework;
import com.pe.ai.entity.StudentCourse;
import com.pe.ai.entity.Submit;
import com.pe.ai.mapper.AiTypeMapper;
import com.pe.ai.mapper.CourseMapper;
import com.pe.ai.mapper.HomeworkMapper;
import com.pe.ai.mapper.StudentCourseMapper;
import com.pe.ai.mapper.SubmitMapper;
import com.pe.ai.service.UserService;
import com.pe.ai.util.RequestValueResolver;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/Homework")
public class HomeworkSubmissionController {

    private final Path storageDir;
    private final String aiBaseUrl;
    private final SubmitMapper submitMapper;
    private final HomeworkMapper homeworkMapper;
    private final CourseMapper courseMapper;
    private final StudentCourseMapper studentCourseMapper;
    private final AiTypeMapper aiTypeMapper;
    private final UserService userService;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient = HttpClient.newHttpClient();

    public HomeworkSubmissionController(@Value("${file.upload-dir:./uploads}") String uploadDir,
                                        @Value("${ai.video.base-url:http://localhost:8000}") String aiBaseUrl,
                                        SubmitMapper submitMapper,
                                        HomeworkMapper homeworkMapper,
                                        CourseMapper courseMapper,
                                        StudentCourseMapper studentCourseMapper,
                                        AiTypeMapper aiTypeMapper,
                                        UserService userService,
                                        ObjectMapper objectMapper) throws IOException {
        this.storageDir = Paths.get(uploadDir).toAbsolutePath().normalize().resolve("homework");
        this.aiBaseUrl = aiBaseUrl.replaceAll("/+$", "");
        this.submitMapper = submitMapper;
        this.homeworkMapper = homeworkMapper;
        this.courseMapper = courseMapper;
        this.studentCourseMapper = studentCourseMapper;
        this.aiTypeMapper = aiTypeMapper;
        this.userService = userService;
        this.objectMapper = objectMapper;
        Files.createDirectories(this.storageDir);
    }

    @PostMapping("/upload_submit")
    public Result<Integer> uploadAndSubmit(@RequestParam("file") MultipartFile file,
                                           @RequestParam("student_id") String studentId,
                                           @RequestParam("course_id") String courseId,
                                           @RequestParam("homework_id") String homeworkIdStr,
                                           @RequestParam(value = "pose_type", required = false) String poseType,
                                           HttpServletRequest request) throws IOException {
        String jwt = RequestValueResolver.resolveJwt(null, request);
        Result<Void> auth = userService.checkJwt(0, studentId, jwt);
        if (auth.getCode() < 0) return Result.error(auth.getCode(), auth.getMessage());

        Homework homework = homeworkMapper.selectById(Integer.parseInt(homeworkIdStr.trim()));
        if (homework == null) return Result.error(-21, "Homework not found");
        if (!courseId.equals(homework.getCourseId())) return Result.error(-10, "Course/Homework mismatch");

        Course course = courseMapper.selectById(homework.getCourseId());
        if (course == null) return Result.error(-21, "Course not found");
        if (Integer.valueOf(2).equals(course.getIsActive())) return Result.error(-22, "Course archived");

        Long enrolled = studentCourseMapper.selectCount(
                new LambdaQueryWrapper<StudentCourse>()
                        .eq(StudentCourse::getStudentId, studentId)
                        .eq(StudentCourse::getCourseId, homework.getCourseId()));
        if (enrolled == null || enrolled == 0) return Result.error(-23, "JWT Error");

        String filename = buildFilename(file.getOriginalFilename());
        Path target = storageDir.resolve(filename).normalize();
        if (!target.startsWith(storageDir)) return Result.error(-10, "Invalid filename");
        Files.copy(file.getInputStream(), target);

        Submit submit = new Submit();
        submit.setStudentId(studentId);
        submit.setHomeworkId(homework.getId());
        submit.setVideoUrl("/Homework/files/" + filename);
        submit.setAiFeedback("AI分析排队中");
        submit.setCreateTime(LocalDateTime.now());
        submitMapper.insert(submit);

        String resolvedPoseType = resolvePoseType(homework.getId(), poseType);
        CompletableFuture.runAsync(() -> processInBackground(submit.getId(), homework.getId(), studentId, resolvedPoseType, target));

        return Result.success(submit.getId());
    }

    @GetMapping("/files/{filename:.+}")
    public ResponseEntity<Resource> getFile(@PathVariable String filename) throws IOException {
        Path file = storageDir.resolve(filename).normalize();
        if (!file.startsWith(storageDir) || !Files.exists(file)) {
            return ResponseEntity.notFound().build();
        }

        Resource resource = new UrlResource(file.toUri());
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType("video/mp4"))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + file.getFileName() + "\"")
                .body(resource);
    }

    private void processInBackground(Integer submitId, Integer homeworkId, String studentId, String poseType, Path videoPath) {
        try {
            callYoloProcess(homeworkId, studentId, poseType, videoPath);
            JsonNode stats = queryYoloStats(homeworkId, studentId, poseType);

            int correctCount = stats.path("correct_count").asInt(0);
            int totalCount = stats.path("total_count").asInt(0);
            int incorrectCount = stats.path("incorrect_count").asInt(0);
            int requiredCount = resolveRequiredCount(homeworkId);
            int score = requiredCount > 0 ? Math.min(100, Math.round(correctCount * 100f / requiredCount)) : 0;

            Submit submit = submitMapper.selectById(submitId);
            if (submit == null) return;
            submit.setVideoUrl("/video/get_processed_video?homework_id=" + homeworkId + "&student_id=" + studentId + "&download=true");
            submit.setScore(score);
            submit.setAiFeedback("AI分析完成：共完成" + totalCount + "次，正确" + correctCount + "次，错误" + incorrectCount + "次。");
            submitMapper.updateById(submit);
        } catch (Exception e) {
            Submit submit = submitMapper.selectById(submitId);
            if (submit != null) {
                submit.setAiFeedback("AI分析失败，已保留原始提交视频。");
                submitMapper.updateById(submit);
            }
        }
    }

    private void callYoloProcess(Integer homeworkId, String studentId, String poseType, Path videoPath) throws Exception {
        String boundary = "----pe-ai-" + UUID.randomUUID();
        byte[] body = multipartBody(boundary, videoPath);
        String url = aiBaseUrl + "/process_and_save_video?homework_id=" + encode(homeworkId.toString())
                + "&student_id=" + encode(studentId)
                + "&pose_type=" + encode(poseType);
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(body))
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IOException("Yolo process failed: " + response.statusCode());
        }
    }

    private JsonNode queryYoloStats(Integer homeworkId, String studentId, String poseType) throws Exception {
        String url = aiBaseUrl + "/query_records?homework_id=" + encode(homeworkId.toString())
                + "&student_id=" + encode(studentId)
                + "&pose_type=" + encode(poseType);
        HttpRequest request = HttpRequest.newBuilder(URI.create(url)).GET().build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IOException("Yolo stats failed: " + response.statusCode());
        }
        JsonNode rows = objectMapper.readTree(response.body());
        return rows.isArray() && !rows.isEmpty() ? rows.get(0) : objectMapper.createObjectNode();
    }

    private byte[] multipartBody(String boundary, Path videoPath) throws IOException {
        String filename = videoPath.getFileName().toString();
        String head = "--" + boundary + "\r\n"
                + "Content-Disposition: form-data; name=\"file\"; filename=\"" + filename + "\"\r\n"
                + "Content-Type: video/mp4\r\n\r\n";
        String tail = "\r\n--" + boundary + "--\r\n";
        byte[] fileBytes = Files.readAllBytes(videoPath);
        byte[] headBytes = head.getBytes(StandardCharsets.UTF_8);
        byte[] tailBytes = tail.getBytes(StandardCharsets.UTF_8);
        byte[] body = new byte[headBytes.length + fileBytes.length + tailBytes.length];
        System.arraycopy(headBytes, 0, body, 0, headBytes.length);
        System.arraycopy(fileBytes, 0, body, headBytes.length, fileBytes.length);
        System.arraycopy(tailBytes, 0, body, headBytes.length + fileBytes.length, tailBytes.length);
        return body;
    }

    private String resolvePoseType(Integer homeworkId, String poseType) {
        if (poseType != null && !poseType.isBlank()) return poseType;
        AiType aiType = aiTypeMapper.selectById(homeworkId);
        return aiType != null && aiType.getType() != null ? aiType.getType() : "pushup";
    }

    private int resolveRequiredCount(Integer homeworkId) {
        AiType aiType = aiTypeMapper.selectById(homeworkId);
        return aiType != null && aiType.getNum() != null ? aiType.getNum() : 0;
    }

    private String buildFilename(String originalFilename) {
        String ext = ".mp4";
        if (originalFilename != null) {
            int dot = originalFilename.lastIndexOf('.');
            if (dot >= 0 && dot < originalFilename.length() - 1) {
                ext = originalFilename.substring(dot).replaceAll("[^A-Za-z0-9.]", "");
            }
        }
        return System.currentTimeMillis() + "_" + UUID.randomUUID().toString().substring(0, 8) + ext;
    }

    private String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
