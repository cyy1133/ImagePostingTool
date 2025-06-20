@echo off
REM 배치 파일 인코딩을 UTF-8로 설정 (한글 주석 및 메시지 표시용)
chcp 65001 > nul

REM Python 설치 여부 확인
echo Python 설치 여부를 확인합니다...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python이 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다.
    echo Python 설치가 필요합니다.
    echo.
    echo 잠시 후 Python 공식 다운로드 페이지가 열립니다.
    echo 설치 후 이 배치 파일을 다시 실행해주세요.
    timeout /t 5 /nobreak > nul
    start "" "https://www.python.org/downloads/"
    goto end
) ELSE (
    echo Python이 설치되어 있습니다.
)

REM Python 스크립트 실행
echo 그림 올리기 프로그램을 실행합니다...
echo 현재 폴더: %~dp0
echo 실행할 스크립트: %~dp0그림올리기.py
echo.

REM 스크립트가 현재 배치 파일과 같은 디렉토리에 있다고 가정
python "Uploader.py"

echo.
echo 프로그램 실행이 완료되었습니다.
echo 아무 키나 누르면 창이 닫힙니다.
pause > nul

:end
exit
