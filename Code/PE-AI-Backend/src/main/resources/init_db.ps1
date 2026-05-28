# PE AI - 数据库初始化脚本
$MYSQL_BIN = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
$DB_NAME = "se_project"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-MysqlScript($Path, $Database = $null) {
    $sourcePath = $Path.Replace('\', '/')
    $args = @("-u", "root", "-pYUSHU750705", "--default-character-set=utf8mb4")
    if ($Database) { $args += $Database }
    $args += @("-e", "source $sourcePath")
    & $MYSQL_BIN @args 2>$null
}

Write-Host "============================================================"
Write-Host " PE AI - 数据库初始化脚本"
Write-Host "============================================================"
Write-Host ""

Write-Host "[1/4] 删除旧数据库..."
& $MYSQL_BIN -u root -pYUSHU750705 -e "DROP DATABASE IF EXISTS $DB_NAME;" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "失败"; exit 1 }
Write-Host "[1/4] 完成"

Write-Host ""
Write-Host "[2/4] 执行建表脚本..."
Invoke-MysqlScript "$SCRIPT_DIR\init_mysql.sql"
if ($LASTEXITCODE -ne 0) { Write-Host "失败"; exit 1 }
Write-Host "[2/4] 完成"

Write-Host ""
Write-Host "[3/4] 导入基础数据..."
Invoke-MysqlScript "$SCRIPT_DIR\data_import.sql" $DB_NAME
if ($LASTEXITCODE -ne 0) { Write-Host "失败"; exit 1 }
Write-Host "[3/4] 完成"

Write-Host ""
Write-Host "[4/4] 导入业务数据..."
Invoke-MysqlScript "$SCRIPT_DIR\seed_data_utf8.sql" $DB_NAME
if ($LASTEXITCODE -ne 0) { Write-Host "失败"; exit 1 }
Write-Host "[4/4] 完成"

Write-Host ""
Write-Host "============================================================"
Write-Host " 初始化完成！"
Write-Host " 教师: 94128 / 123456"
Write-Host " 学生: 2359086 / 123456"
Write-Host "============================================================"
