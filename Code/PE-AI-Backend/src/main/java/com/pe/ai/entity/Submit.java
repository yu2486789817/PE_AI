package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("submit")
public class Submit {
    @TableId(type = IdType.AUTO)
    private Integer id;
    private Integer homeworkId;
    private String studentId;
    private String videoUrl;
    private Integer score;
    private String aiFeedback;
    private String teacherFeedback;
    private LocalDateTime createTime;
}
