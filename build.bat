@echo off
chcp 65001
setlocal EnableDelayedExpansion

echo 开始更新 PyQt5 资源文件和翻译文件...

REM 设置文件路径
set "QRC_PATH=interface\resource\resource.qrc"
set "TS_PATH=interface\resource\i18n\gallery.zh_CN.ts"
set "OUTPUT_PY=interface\common\resource.py"
set "OUTPUT_QM=interface\resource\i18n\gallery.zh_CN.qm"

REM 检查 pyrcc5 是否可用
where pyrcc5 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: pyrcc5 未找到，请确保 PyQt5 已正确安装并添加到 PATH。
    goto :error
)

REM 检查 lrelease 是否可用
where lrelease >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: lrelease 未找到，请确保 PyQt5 已正确安装并添加到 PATH。
    goto :error
)

REM 更新 resource.qrc -> resource.py
if exist "%QRC_PATH%" (
    echo 正在转换 %QRC_PATH% 为 %OUTPUT_PY%...
    pyrcc5 "%QRC_PATH%" -o "%OUTPUT_PY%"
    if %ERRORLEVEL% equ 0 (
        echo 成功生成 %OUTPUT_PY%
    ) else (
        echo 错误: 转换 %QRC_PATH% 失败
        goto :error
    )
) else (
    echo 错误: %QRC_PATH% 不存在
    goto :error
)

REM 更新 gallery.zh_CN.ts -> gallery.zh_CN.qm
if exist "%TS_PATH%" (
    echo 正在转换 %TS_PATH% 为 %OUTPUT_QM%...
    lrelease "%TS_PATH%" -qm "%OUTPUT_QM%"
    if %ERRORLEVEL% equ 0 (
        echo 成功生成 %OUTPUT_QM%
    ) else (
        echo 错误: 转换 %TS_PATH% 失败
        goto :error
    )
) else (
    echo 错误: %TS_PATH% 不存在
    goto :error
)

echo 所有文件更新完成！
goto :end

:error
echo 更新过程中出现错误，请检查路径和工具配置。
pause
exit /b 1

:end
pause
exit /b 0