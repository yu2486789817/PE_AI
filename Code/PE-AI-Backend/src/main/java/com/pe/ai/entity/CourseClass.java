package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("class") // MySQL class table
public class CourseClass {
    @TableId(type = IdType.AUTO)
    private Integer id;
    private String courseId;
    private String title;
    private String description;
    private String contentUrl;
    private LocalDateTime createTime;
}
