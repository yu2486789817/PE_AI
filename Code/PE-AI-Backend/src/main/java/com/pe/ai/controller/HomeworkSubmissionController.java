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
import com.pe.ai.service.SupabaseStorageService;
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
    private final SupabaseStorageService supabaseStorage;
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
                                        SupabaseStorageService supabaseStorage,
                                        ObjectMapper objectMapper) throws IOException {
        this.storageDir = Paths.get(uploadDir).toAbsolutePath().normalize().resolve("homework");
        this.aiBaseUrl = aiBaseUrl.replaceAll("/+$", "");
        this.submitMapper = submitMapper;
        this.homeworkMapper = homeworkMapper;
        this.courseMapper = courseMapper;
        this.studentCourseMapper = studentCourseMapper;
        this.aiTypeMapper = aiTypeMapper;
        this.userService = userService;
        this.supabaseStorage = supabaseStorage;
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
        // 本地保存一份原始视频，供后台转发给 Yolo 分析使用
        Files.copy(file.getInputStream(), target);

        // 配置了 Supabase 时，原始视频同时上传到云端做持久化，避免临时磁盘清理后丢失
        String originalVideoUrl = "/Homework/files/" + filename;
        if (supabaseStorage.isEnabled()) {
            try {
                String objectName = "homework/" + filename;
                originalVideoUrl = supabaseStorage.upload(
                        objectName, Files.newInputStream(target), Files.size(target), "video/mp4");
            } catch (Exception e) {
                // 云上传失败不阻断提交，回退到本地 URL
                originalVideoUrl = "/Homework/files/" + filename;
            }
        }

        Submit submit = new Submit();
        submit.setStudentId(studentId);
        submit.setHomeworkId(homework.getId());
        submit.setVideoUrl(originalVideoUrl);
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
            // 1) 触发 YOLO 处理（不等 SSE 流读完，避免被 Render/隧道的长连接超时打断）。
            //    YOLO 内部异步处理后会把结果写进自己的 SQLite，下面通过轮询 /query_records 拿到结果。
            triggerYoloProcess(homeworkId, studentId, poseType, videoPath);

            // 2) 轮询 YOLO 统计结果，最多等待 ~5 分钟。
            JsonNode stats = pollYoloStats(homeworkId, studentId, poseType);

            int correctCount = stats.path("correct_count").asInt(0);
            int totalCount = stats.path("total_count").asInt(0);
            int incorrectCount = stats.path("incorrect_count").asInt(0);
            int requiredCount = resolveRequiredCount(homeworkId);
            int score = requiredCount > 0 ? Math.min(100, Math.round(correctCount * 100f / requiredCount)) : 0;

            Submit submit = submitMapper.selectById(submitId);
            if (submit == null) return;
            // 优先使用 YOLO 上传到 Supabase 的公共 URL（前端直连播放）；
            // 兜底回退到通过 Render→cloudflared 代理的老路径。
            String processedVideoUrl = extractProcessedVideoUrl(stats);
            if (processedVideoUrl == null || processedVideoUrl.isBlank()) {
                processedVideoUrl = "/video/get_processed_video?homework_id=" + homeworkId
                        + "&student_id=" + studentId + "&download=true";
            }
            submit.setVideoUrl(processedVideoUrl);
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

    /** 从 /query_records 返回的记录里抽取 feedback_json.processed_video_url。 */
    private String extractProcessedVideoUrl(JsonNode stats) {
        JsonNode raw = stats.path("feedback_json");
        if (raw.isMissingNode() || raw.isNull()) return null;
        try {
            JsonNode feedback = raw.isTextual() ? objectMapper.readTree(raw.asText()) : raw;
            String url = feedback.path("processed_video_url").asText("");
            return url.isBlank() ? null : url;
        } catch (Exception ignored) {
            return null;
        }
    }

    /**
     * 把视频 POST 给 YOLO 触发处理，不等 SSE 流读完。
     * 通过 async_mode=true 让 YOLO 立即 202 返回，把生成器塞到自己的后台任务里跑完。
     * 结果会写进 YOLO 的 SQLite，下面通过轮询 /query_records 拿到。
     */
    private void triggerYoloProcess(Integer homeworkId, String studentId, String poseType, Path videoPath) throws Exception {
        String boundary = "----pe-ai-" + UUID.randomUUID();
        byte[] body = multipartBody(boundary, videoPath);
        String url = aiBaseUrl + "/process_and_save_video?homework_id=" + encode(homeworkId.toString())
                + "&student_id=" + encode(studentId)
                + "&pose_type=" + encode(poseType)
                + "&async_mode=true";
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .timeout(java.time.Duration.ofSeconds(120))
                .POST(HttpRequest.BodyPublishers.ofByteArray(body))
                .build();
        HttpResponse<Void> response = httpClient.send(request, HttpResponse.BodyHandlers.discarding());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IOException("Yolo process failed: " + response.statusCode());
        }
    }

    /**
     * 轮询 /query_records 直到 YOLO 写出非空记录，最多等待 ~5 分钟。
     */
    private JsonNode pollYoloStats(Integer homeworkId, String studentId, String poseType) throws Exception {
        long deadline = System.currentTimeMillis() + 5 * 60 * 1000L;
        long intervalMs = 3000L;
        Exception lastException = null;
        while (System.currentTimeMillis() < deadline) {
            try {
                JsonNode stats = queryYoloStats(homeworkId, studentId, poseType);
                if (stats != null && stats.has("total_count")) {
                    return stats;
                }
            } catch (Exception e) {
                lastException = e;
            }
            Thread.sleep(intervalMs);
        }
        throw new IOException("Yolo poll timeout (5 min)", lastException);
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
