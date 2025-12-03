@echo off
setlocal
echo Syncing dev branch with master after PR merge...
echo.

echo Fetching latest changes from remote...
call git fetch github
if errorlevel 1 (
    echo Error: Failed to fetch from remote
    exit /b 1
)

echo.
echo Updating master to latest from remote...
call git checkout master
if errorlevel 1 (
    echo Error: Failed to checkout master
    exit /b 1
)
call git pull github master
if errorlevel 1 (
    echo Error: Failed to pull master
    exit /b 1
)

echo.
echo Resetting dev to master...
call git checkout dev
if errorlevel 1 (
    echo Error: Failed to checkout dev
    exit /b 1
)
call git reset --hard master
if errorlevel 1 (
    echo Error: Failed to reset dev to master
    exit /b 1
)

echo.
echo Fetching dev branch reference from remote...
call git fetch github dev

echo.
echo Pushing dev to remote...
call git push github dev --force
if errorlevel 1 (
    echo Error: Failed to push dev to remote
    exit /b 1
)

echo.
echo Done! Dev branch is now synced with master.
call git log --oneline --graph --all --decorate -5
endlocal
