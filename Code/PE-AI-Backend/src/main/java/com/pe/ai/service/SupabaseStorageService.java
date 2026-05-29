package com.pe.ai.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;

import java.io.InputStream;
import java.util.List;
import java.util.Map;

/**
 * 通过 Supabase Storage REST API 持久化教学视频文件。
 * 仅当配置了 supabase.url 和 supabase.service-key 时启用，否则由调用方回退到本地磁盘存储。
 * 所有密钥从环境变量读取，不在代码中硬编码。
 */
@Service
public class SupabaseStorageService {

    private final String supabaseUrl;
    private final String serviceKey;
    private final String bucket;
    private final RestClient restClient;

    public SupabaseStorageService(
            @Value("${supabase.url:}") String supabaseUrl,
            @Value("${supabase.service-key:}") String serviceKey,
            @Value("${supabase.bucket:teaching-videos}") String bucket) {
        this.supabaseUrl = trimTrailingSlash(supabaseUrl);
        this.serviceKey = serviceKey == null ? "" : serviceKey.trim();
        this.bucket = bucket;
        this.restClient = RestClient.builder().build();
    }

    /** 是否已配置 Supabase Storage（决定使用云存储还是本地磁盘）。 */
    public boolean isEnabled() {
        return StringUtils.hasText(supabaseUrl) && StringUtils.hasText(serviceKey);
    }

    /** 上传文件，返回可直接访问的公共 URL。 */
    public String upload(String objectName, InputStream content, long size, String contentType) {
        MediaType mediaType = contentType != null
                ? MediaType.parseMediaType(contentType)
                : MediaType.APPLICATION_OCTET_STREAM;

        restClient.post()
                .uri(supabaseUrl + "/storage/v1/object/" + bucket + "/" + objectName)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + serviceKey)
                .header("x-upsert", "true")
                .contentType(mediaType)
                .body(new InputStreamResource(content) {
                    @Override
                    public long contentLength() {
                        return size;
                    }
                })
                .retrieve()
                .toBodilessEntity();

        return publicUrl(objectName);
    }

    /** 删除文件。 */
    public void delete(String objectName) {
        restClient.delete()
                .uri(supabaseUrl + "/storage/v1/object/" + bucket + "/" + objectName)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + serviceKey)
                .retrieve()
                .toBodilessEntity();
    }

    /** 列出 bucket 内的对象（含 name 与 metadata.size / metadata.mimetype 等）。 */
    public List<Map<String, Object>> list() {
        Map<String, Object> requestBody = Map.of(
                "prefix", "",
                "limit", 1000,
                "sortBy", Map.of("column", "created_at", "order", "desc"));

        List<Map<String, Object>> result = restClient.post()
                .uri(supabaseUrl + "/storage/v1/object/list/" + bucket)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + serviceKey)
                .contentType(MediaType.APPLICATION_JSON)
                .body(requestBody)
                .retrieve()
                .body(new ParameterizedTypeReference<List<Map<String, Object>>>() {});

        return result == null ? List.of() : result;
    }

    /** 文件的公共访问 URL（bucket 需设为 public）。 */
    public String publicUrl(String objectName) {
        return supabaseUrl + "/storage/v1/object/public/" + bucket + "/" + objectName;
    }

    private static String trimTrailingSlash(String url) {
        if (url == null) return "";
        String trimmed = url.trim();
        return trimmed.endsWith("/") ? trimmed.substring(0, trimmed.length() - 1) : trimmed;
    }
}
