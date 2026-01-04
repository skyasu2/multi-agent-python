@echo off
echo [TEST] Running All Tests and Generating Report...

:: Create reports directory if not exists
if not exist "reports" mkdir reports

:: Run pytest with HTML report generation
:: --self-contained-html: CSS/JS를 HTML 파일 하나에 포함 (공유 용이)
pytest tests/ --html=reports/test_report.html --self-contained-html --asyncio-mode=auto

echo.
echo ========================================================
echo [DONE] Test Report Generated: reports/test_report.html
echo ========================================================
pause
