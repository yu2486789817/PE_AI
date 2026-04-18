@echo off
chcp 65001 >nul
echo ============================================================
echo  PE AI - 数据库初始化脚本
echo ============================================================
echo.

set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
set DB_NAME=se_project

echo [1/3] 删除旧数据库...
%MYSQL_BIN% -u root -pYUSHU750705 -e "DROP DATABASE IF EXISTS %DB_NAME%;"
if errorlevel 1 (
    echo 数据库操作失败
    pause
    exit /b 1
)
echo [1/3] 完成

echo.
echo [2/3] 执行建表脚本...
%MYSQL_BIN% -u root -pYUSHU750705 -e "source %~dp0init_mysql.sql"
if errorlevel 1 (
    echo 建表失败
    pause
    exit /b 1
)
echo [2/3] 完成

echo.
echo [3/3] 导入基础数据...
%MYSQL_BIN% -u root -pYUSHU750705 -e "source %~dp0data_import.sql"
if errorlevel 1 (
    echo 基础数据导入失败
    pause
    exit /b 1
)
echo [3/3] 完成

echo.
echo [4/4] 导入业务数据...
%MYSQL_BIN% -u root -pYUSHU750705 -e "source %~dp0seed_data_utf8.sql"
if errorlevel 1 (
    echo 业务数据导入失败
    pause
    exit /b 1
)
echo [4/4] 完成

echo.
echo ============================================================
echo  初始化完成！
echo  教师: 94128 / 123456
echo  学生: 2359086 / 123456
echo ============================================================
pause
