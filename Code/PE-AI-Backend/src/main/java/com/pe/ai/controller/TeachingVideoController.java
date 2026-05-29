package com.pe.ai.controller;

import com.pe.ai.service.SupabaseStorageService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.text.DecimalFormat;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Stream;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping("/Teaching-video")
public class TeachingVideoController {

    private static final Set<String> ALLOWED_EXTENSIONS = Set.of(
            "mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v", "mpg", "mpeg", "3gp"
    );
    private static final long MAX_FILE_SIZE_BYTES = 2L * 1024 * 1024 * 1024;
    private static final DateTimeFormatter FILENAME_TIME = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
    private static final DateTimeFormatter DISPLAY_TIME = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final Path storageDir;
    private final SupabaseStorageService supabaseStorage;

    public TeachingVideoController(@Value("${file.upload-dir:./uploads}") String uploadDir,
                                   SupabaseStorageService supabaseStorage) throws IOException {
        this.storageDir = Paths.get(uploadDir).toAbsolutePath().normalize().resolve("videos");
        Files.createDirectories(this.storageDir);
        this.supabaseStorage = supabaseStorage;
    }

    @PostMapping("/upload")
    public ResponseEntity<Map<String, Object>> upload(@RequestParam("file") MultipartFile file,
                                                      HttpServletRequest request) throws IOException {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(error("Empty file"));
        }

        String originalName = StringUtils.cleanPath(file.getOriginalFilename() == null ? "" : file.getOriginalFilename());
        String extension = getExtension(originalName);
        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            return ResponseEntity.badRequest().body(error("Unsupported file type"));
        }

        if (file.getSize() > MAX_FILE_SIZE_BYTES) {
            return ResponseEntity.badRequest().body(error("File too large!"));
        }

        String filename = FILENAME_TIME.format(LocalDateTime.now()) + "_"
                + UUID.randomUUID().toString().replace("-", "").substring(0, 8) + "." + extension;

        String url;
        if (supabaseStorage.isEnabled()) {
            // 云存储：上传到 Supabase Storage，返回持久公共 URL
            String contentType = file.getContentType();
            url = supabaseStorage.upload(filename, file.getInputStream(), file.getSize(), contentType);
        } else {
            // 本地磁盘回退（开发环境）
            Path target = storageDir.resolve(filename).normalize();
            if (!target.startsWith(storageDir)) {
                return ResponseEntity.badRequest().body(error("Invalid filename"));
            }
            Files.copy(file.getInputStream(), target, StandardCopyOption.REPLACE_EXISTING);
            url = buildFileUrl(request, filename);
        }

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("success", true);
        body.put("filename", filename);
        body.put("url", url);
        return ResponseEntity.ok(body);
    }

    @GetMapping("/files/{filename:.+}")
    public ResponseEntity<Resource> getFile(@PathVariable String filename) throws IOException {
        // 云存储模式：重定向到 Supabase 公共 URL（兼容旧的相对路径链接）
        if (supabaseStorage.isEnabled()) {
            String clean = Paths.get(filename).getFileName().toString();
            return ResponseEntity.status(302)
                    .location(URI.create(supabaseStorage.publicUrl(clean)))
                    .build();
        }

        Path file = resolveExistingFile(filename);
        Resource resource = toResource(file);
        String contentType = Files.probeContentType(file);
        if (contentType == null) {
            contentType = MediaType.APPLICATION_OCTET_STREAM_VALUE;
        }
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + file.getFileName() + "\"")
                .contentType(MediaType.parseMediaType(contentType))
                .body(resource);
    }

    @GetMapping("/info")
    public Map<String, Object> info(HttpServletRequest request) throws IOException {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("success", true);
        body.put("storage", supabaseStorage.isEnabled() ? "supabase" : "local");
        body.put("server_ip", request.getServerName());
        body.put("server_port", request.getServerPort());
        if (!supabaseStorage.isEnabled()) {
            body.put("disk_free_gb", formatGb(Files.getFileStore(storageDir).getUsableSpace()));
        }
        body.put("max_file_size_gb", 2.0);
        body.put("allowed_extensions", ALLOWED_EXTENSIONS);
        return body;
    }

    @GetMapping("/list")
    public Map<String, Object> list(HttpServletRequest request) throws IOException {
        List<Map<String, Object>> files;
        if (supabaseStorage.isEnabled()) {
            files = supabaseStorage.list().stream()
                    .filter(obj -> obj.get("name") != null)
                    .map(this::toSupabaseFileInfo)
                    .toList();
        } else {
            try (Stream<Path> stream = Files.list(storageDir)) {
                files = stream
                        .filter(Files::isRegularFile)
                        .sorted(Comparator.comparing(this::lastModified).reversed())
                        .map(path -> toFileInfo(path, request))
                        .toList();
            }
        }

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("success", true);
        body.put("files", files);
        return body;
    }

    @DeleteMapping("/delete/{filename:.+}")
    public ResponseEntity<Map<String, Object>> delete(@PathVariable String filename) throws IOException {
        String name;
        if (supabaseStorage.isEnabled()) {
            name = Paths.get(filename).getFileName().toString();
            supabaseStorage.delete(name);
        } else {
            Path file = resolveExistingFile(filename);
            Files.delete(file);
            name = file.getFileName().toString();
        }

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("success", true);
        body.put("filename", name);
        return ResponseEntity.ok(body);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> toSupabaseFileInfo(Map<String, Object> obj) {
        Map<String, Object> file = new LinkedHashMap<>();
        String name = String.valueOf(obj.get("name"));
        file.put("filename", name);

        Object metaObj = obj.get("metadata");
        long size = 0L;
        if (metaObj instanceof Map<?, ?> meta) {
            Object sizeVal = ((Map<String, Object>) meta).get("size");
            if (sizeVal instanceof Number num) {
                size = num.longValue();
            }
        }
        file.put("size", size);
        file.put("modified", obj.getOrDefault("created_at", ""));
        file.put("url", supabaseStorage.publicUrl(name));
        return file;
    }

    private Map<String, Object> toFileInfo(Path path, HttpServletRequest request) {
        Map<String, Object> file = new LinkedHashMap<>();
        file.put("filename", path.getFileName().toString());
        try {
            file.put("size", Files.size(path));
            file.put("modified", DISPLAY_TIME.format(LocalDateTime.ofInstant(Instant.ofEpochMilli(lastModified(path)), ZoneId.systemDefault())));
        } catch (IOException e) {
            file.put("size", 0L);
            file.put("modified", "");
        }
        file.put("url", buildFileUrl(request, path.getFileName().toString()));
        return file;
    }

    private long lastModified(Path path) {
        try {
            return Files.getLastModifiedTime(path).toMillis();
        } catch (IOException e) {
            return 0L;
        }
    }

    private Path resolveExistingFile(String filename) throws IOException {
        String clean = Paths.get(filename).getFileName().toString();
        Path file = storageDir.resolve(clean).normalize();
        if (!file.startsWith(storageDir) || !Files.exists(file) || !Files.isRegularFile(file)) {
            throw new ResponseStatusException(NOT_FOUND, "File not found");
        }
        return file;
    }

    private Resource toResource(Path file) throws MalformedURLException {
        return new UrlResource(file.toUri());
    }

    private String buildFileUrl(HttpServletRequest request, String filename) {
        return request.getScheme() + "://" + request.getServerName() + ":" + request.getServerPort()
                + "/Teaching-video/files/" + filename;
    }

    private String getExtension(String filename) {
        int dot = filename.lastIndexOf('.');
        return dot >= 0 ? filename.substring(dot + 1).toLowerCase(Locale.ROOT) : "";
    }

    private double formatGb(long bytes) {
        double value = bytes / 1024d / 1024d / 1024d;
        return Double.parseDouble(new DecimalFormat("0.0#").format(value));
    }

    private Map<String, Object> error(String message) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("success", false);
        body.put("error", message);
        return body;
    }
}
