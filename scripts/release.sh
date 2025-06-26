#!/bin/bash

# Alfred Workflow 发布脚本
# 用法: ./scripts/release.sh [版本号]
# 例如: ./scripts/release.sh 0.1.0

set -e

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <版本号>"
    echo "例如: $0 0.1.0"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"

# 验证版本号格式
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "错误: 版本号格式不正确，应为 x.y.z 格式"
    exit 1
fi

echo "准备发布版本: $TAG"

# 检查是否在git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "错误: 当前目录不是git仓库"
    exit 1
fi

# 检查工作目录是否干净
if ! git diff-index --quiet HEAD --; then
    echo "错误: 工作目录有未提交的更改，请先提交所有更改"
    exit 1
fi

# 检查是否在主分支
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo "警告: 当前不在主分支 ($CURRENT_BRANCH)，是否继续? (y/N)"
    read -r response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
        echo "取消发布"
        exit 1
    fi
fi

# 检查标签是否已存在
if git tag -l | grep -q "^$TAG$"; then
    echo "错误: 标签 $TAG 已存在"
    exit 1
fi

# 更新info.plist中的版本号
echo "更新 info.plist 中的版本号..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/<string>[0-9]\+\.[0-9]\+\.[0-9]\+<\/string>/<string>$VERSION<\/string>/g" src/info.plist
else
    # Linux
    sed -i "s/<string>[0-9]\+\.[0-9]\+\.[0-9]\+<\/string>/<string>$VERSION<\/string>/g" src/info.plist
fi

# 验证更新
if grep -q "<string>$VERSION</string>" src/info.plist; then
    echo "✅ 版本号已更新到 $VERSION"
else
    echo "❌ 版本号更新失败"
    exit 1
fi

# 提交版本更新
echo "提交版本更新..."
git add src/info.plist
git commit -m "chore: bump version to $VERSION"

# 创建标签
echo "创建标签 $TAG..."
git tag -a "$TAG" -m "Release $TAG"

# 推送到远程
echo "推送到远程仓库..."
git push origin "$CURRENT_BRANCH"
git push origin "$TAG"

echo ""
echo "🎉 版本 $TAG 发布成功!"
echo ""
echo "GitHub Actions 将自动构建并创建 Release。"
echo "请访问 https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/actions 查看构建状态。"
echo ""
echo "发布完成后，用户可以从以下地址下载:"
echo "https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/releases/tag/$TAG"