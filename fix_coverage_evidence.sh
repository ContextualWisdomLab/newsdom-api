# Check if there is an issue with out of sync branches
git fetch origin develop
git rebase origin/develop
