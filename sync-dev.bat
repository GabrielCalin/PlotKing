@echo off
echo Syncing dev branch with master after PR merge...
echo.

echo Fetching latest changes from remote...
git fetch github

echo.
echo Updating master to latest from remote...
git checkout master
git pull github master

echo.
echo Resetting dev to master...
git checkout dev
git reset --hard master

echo.
echo Fetching dev branch reference from remote...
git fetch github dev

echo.
echo Pushing dev to remote...
git push github dev --force

echo.
echo Done! Dev branch is now synced with master.
git log --oneline --graph --all --decorate -5
