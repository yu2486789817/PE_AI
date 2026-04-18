package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("std_teacher")
public class StdTeacher {
    @TableId
    private String id;
    private String name;
}
