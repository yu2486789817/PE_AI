package com.pe.ai.controller;

import com.pe.ai.common.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        return Result.success(Map.of(
                "status", "UP",
                "time", LocalDateTime.now().toString(),
                "service", "PE AI Manager Backend (Spring Boot)"
        ));
    }
}
