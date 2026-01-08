@echo off
setlocal
echo Squashing commits after github/dev to staging area...
echo.

echo Fetching latest changes from remote...
call git fetch github
if errorlevel 1 (
    echo Error: Failed to fetch from remote
    exit /b 1
)

echo.
echo Checking if github/dev exists...
call git rev-parse --verify github/dev >nul 2>&1
if errorlevel 1 (
    echo Error: github/dev branch not found. Make sure the remote is configured correctly.
    exit /b 1
)

echo.
echo Current branch: 
call git branch --show-current

echo.
echo Current HEAD commit:
call git log --oneline -1

echo.
echo github/dev commit:
call git log --oneline -1 github/dev

echo.
echo Checking for commits to squash...
for /f %%i in ('git rev-list --count github/dev..HEAD') do set COMMIT_COUNT=%%i

if "%COMMIT_COUNT%"=="0" (
    echo No commits found after github/dev. Nothing to squash.
    exit /b 0
)

echo.
echo Found %COMMIT_COUNT% commit(s) after github/dev
echo.
echo Commits that will be moved to staging:
call git log --oneline github/dev..HEAD

echo.
set /p CONFIRM="Do you want to proceed? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Operation cancelled.
    exit /b 0
)

echo.
echo Resetting to github/dev (soft reset - keeping changes in staging)...
call git reset --soft github/dev
if errorlevel 1 (
    echo Error: Failed to reset to github/dev
    exit /b 1
)

echo.
echo Done! All commits have been moved to staging area.
echo.
echo Current status:
call git status --short

echo.
echo You can now review the changes and create a single commit with:
echo   git commit -m "Your commit message"
echo.
endlocal

