package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("student")
public class Student {
    @TableId
    private String id;
    private String password;
    private String name;
    private String gender;
    private String college;
    private String department;
    private String major;
    private LocalDateTime createdTime;
    private LocalDateTime loginTime;
}
