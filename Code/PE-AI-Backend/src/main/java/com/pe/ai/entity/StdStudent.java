package com.pe.ai.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("std_student")
public class StdStudent {
    @TableId
    private String id;
    private String name;
}
