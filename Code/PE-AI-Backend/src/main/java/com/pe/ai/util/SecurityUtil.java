package com.pe.ai.util;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class SecurityUtil {

    private static final DateTimeFormatter JWT_TIME_FMT = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");
    private static final long JWT_EXPIRE_MINUTES = 120; // 2 hours

    /**
     * SHA-256 hash, compatible with the original .NET Basic_calculate.ComputeSHA256
     */
    public static String computeSHA256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }

    /**
     * Generate JWT token compatible with the original .NET format:
     * token = timestamp(14) + SHA256(timestamp + id + password)
     */
    public static String generateToken(String id, String password) {
        String timestamp = LocalDateTime.now().format(JWT_TIME_FMT);
        String raw = timestamp + id + password;
        String hash = computeSHA256(raw);
        return timestamp + hash;
    }

    /**
     * Validate JWT token:
     * 1. Extract timestamp from first 14 chars
     * 2. Recompute SHA256(timestamp + id + password) and compare
     * 3. Check if token has expired
     */
    public static boolean validateToken(String token, String id, String password) {
        if (token == null || token.length() < 15) {
            return false;
        }
        String jwtTime = token.substring(0, 14);
        String expectedHash = computeSHA256(jwtTime + id + password);
        String expectedToken = jwtTime + expectedHash;

        if (!expectedToken.equals(token)) {
            return false;
        }
        return !isTokenExpired(jwtTime);
    }

    /**
     * Check if the token timestamp has expired (same as Basic_calculate.Check_login_time)
     */
    public static boolean isTokenExpired(String jwtTime) {
        try {
            LocalDateTime tokenTime = LocalDateTime.parse(jwtTime, JWT_TIME_FMT);
            return LocalDateTime.now().isAfter(tokenTime.plusMinutes(JWT_EXPIRE_MINUTES));
        } catch (Exception e) {
            return true;
        }
    }
}
