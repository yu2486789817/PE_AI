package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("student_course")
public class StudentCourse {
    @TableId(type = IdType.AUTO)
    private Integer id;
    private String studentId;
    private String courseId;
    private LocalDateTime joinedTime;
}
