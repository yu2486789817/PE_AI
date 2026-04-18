package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("course")
public class Course {
    @TableId
    private String id;
    private String teacherId;
    private String name;
    private String info;
    private String code;
    private Integer semester;
    private Integer isActive;
    private LocalDateTime createdTime;
}
