package com.pe.ai.util;

import jakarta.servlet.http.HttpServletRequest;

import java.util.Map;

public final class RequestValueResolver {

    private RequestValueResolver() {
    }

    public static String getIgnoreCase(Map<String, String> body, String... keys) {
        if (body == null || keys == null) {
            return null;
        }
        for (String key : keys) {
            if (key == null) {
                continue;
            }
            String direct = body.get(key);
            if (direct != null) {
                return direct;
            }
            for (Map.Entry<String, String> entry : body.entrySet()) {
                if (key.equalsIgnoreCase(entry.getKey())) {
                    return entry.getValue();
                }
            }
        }
        return null;
    }

    public static String normalizeBearerToken(String token) {
        if (token == null) {
            return null;
        }
        String normalized = token.trim();
        if (normalized.isEmpty()) {
            return null;
        }
        if (normalized.regionMatches(true, 0, "Bearer ", 0, 7)) {
            normalized = normalized.substring(7).trim();
        }
        return normalized.isEmpty() ? null : normalized;
    }

    private static boolean isLikelyToken(String s) {
        if (s == null) return false;
        String val = s.trim();
        if (val.length() >= 78 && val.substring(0, 14).matches("\\d{14}")) {
            return true;
        }
        return val.length() >= 40;
    }

    public static String resolveJwt(Map<String, String> body, HttpServletRequest request) {
        // 1. Try explicit JWT/token keys first
        String jwt = getIgnoreCase(body, "jwt", "token", "authorization");
        if (jwt != null && !jwt.isBlank()) {
            return normalizeBearerToken(jwt);
        }

        // 2. Prioritize positional parameter that actually looks like a token
        String third = getIgnoreCase(body, "third");
        String second = getIgnoreCase(body, "second");

        if (isLikelyToken(third)) {
            jwt = third;
        } else if (isLikelyToken(second)) {
            jwt = second;
        } else if (third != null && !third.isBlank()) {
            jwt = third;
        } else {
            jwt = second;
        }

        if ((jwt == null || jwt.isBlank()) && request != null) {
            jwt = request.getHeader("Authorization");
        }
        return normalizeBearerToken(jwt);
    }
}
