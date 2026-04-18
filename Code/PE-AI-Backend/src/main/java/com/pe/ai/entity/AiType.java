package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("ai_type")
public class AiType {
    @TableId
    private Integer homeworkId;
    private String type;
    private Integer num;
}
