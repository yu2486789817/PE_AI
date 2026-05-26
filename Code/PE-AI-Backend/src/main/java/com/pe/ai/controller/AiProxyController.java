package com.pe.ai.controller;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.ResponseErrorHandler;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.net.URI;
import java.util.Collections;
import java.util.Set;

@RestController
public class AiProxyController {

    private static final Set<String> HOP_BY_HOP_HEADERS = Set.of(
            "connection",
            "content-length",
            "host",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailer",
            "transfer-encoding",
            "upgrade"
    );

    private final RestTemplate restTemplate;
    private final String chatBaseUrl;
    private final String videoBaseUrl;

    public AiProxyController(@Value("${ai.chat.base-url:http://localhost:5000}") String chatBaseUrl,
                             @Value("${ai.video.base-url:http://localhost:8000}") String videoBaseUrl) {
        this.restTemplate = new RestTemplate();
        this.restTemplate.setErrorHandler(new PassthroughErrorHandler());
        this.chatBaseUrl = trimTrailingSlash(chatBaseUrl);
        this.videoBaseUrl = trimTrailingSlash(videoBaseUrl);
    }

    @RequestMapping({"/chat", "/chat/**"})
    public ResponseEntity<byte[]> proxyChat(HttpServletRequest request) throws IOException {
        return proxy(request, "/chat", chatBaseUrl);
    }

    @RequestMapping({"/video", "/video/**"})
    public ResponseEntity<byte[]> proxyVideo(HttpServletRequest request) throws IOException {
        return proxy(request, "/video", videoBaseUrl);
    }

    private ResponseEntity<byte[]> proxy(HttpServletRequest request, String prefix, String baseUrl) throws IOException {
        URI targetUri = URI.create(baseUrl + downstreamPath(request, prefix));
        HttpHeaders requestHeaders = copyRequestHeaders(request);
        byte[] requestBody = request.getInputStream().readAllBytes();

        ResponseEntity<byte[]> response = restTemplate.exchange(
                targetUri,
                HttpMethod.valueOf(request.getMethod()),
                new HttpEntity<>(requestBody, requestHeaders),
                byte[].class
        );

        HttpHeaders responseHeaders = copyResponseHeaders(response.getHeaders());
        return ResponseEntity
                .status(response.getStatusCode())
                .headers(responseHeaders)
                .body(response.getBody());
    }

    private String downstreamPath(HttpServletRequest request, String prefix) {
        String path = request.getRequestURI().substring(request.getContextPath().length());
        String downstreamPath = path.length() > prefix.length() ? path.substring(prefix.length()) : "/";
        String query = request.getQueryString();
        return query == null || query.isBlank() ? downstreamPath : downstreamPath + "?" + query;
    }

    private HttpHeaders copyRequestHeaders(HttpServletRequest request) {
        HttpHeaders headers = new HttpHeaders();
        Collections.list(request.getHeaderNames()).forEach(name -> {
            if (!HOP_BY_HOP_HEADERS.contains(name.toLowerCase())) {
                headers.put(name, Collections.list(request.getHeaders(name)));
            }
        });
        return headers;
    }

    private HttpHeaders copyResponseHeaders(HttpHeaders source) {
        HttpHeaders headers = new HttpHeaders();
        source.forEach((name, values) -> {
            if (!HOP_BY_HOP_HEADERS.contains(name.toLowerCase())) {
                headers.put(name, values);
            }
        });
        return headers;
    }

    private static String trimTrailingSlash(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }

    private static class PassthroughErrorHandler implements ResponseErrorHandler {
        @Override
        public boolean hasError(org.springframework.http.client.ClientHttpResponse response) {
            return false;
        }

        @Override
        public void handleError(org.springframework.http.client.ClientHttpResponse response) {
        }
    }
}
