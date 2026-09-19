# We don't actually push to remote directly, we just make a commit locally
# since `submit` handles the commit message logic and branch name.

git checkout -b bolt/defaultdict-optimization || git checkout bolt/defaultdict-optimization
