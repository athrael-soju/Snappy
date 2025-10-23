#!/bin/bash
# Create a new release tag and push to GitHub
# This will trigger the release-please workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version from package.json
CURRENT_VERSION=$(node -p "require('./frontend/package.json').version")

echo -e "${GREEN}Current version: ${CURRENT_VERSION}${NC}"
echo ""
echo "This script helps you create a new release using conventional commits."
echo "Release Please will automatically determine the next version based on your commits."
echo ""
echo "Commit message format:"
echo "  feat: adds new feature (minor version bump)"
echo "  fix: bug fix (patch version bump)"
echo "  feat!: breaking change (major version bump)"
echo "  docs: documentation updates (no version bump)"
echo ""

# Check if there are uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}You have uncommitted changes. Please commit or stash them first.${NC}"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo -e "${YELLOW}Warning: You are on branch '${CURRENT_BRANCH}', not 'main'.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Show recent commits
echo -e "${GREEN}Recent commits:${NC}"
git log --oneline --decorate -10
echo ""

# Push to trigger release-please
read -p "Push to GitHub to trigger release workflow? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin "$CURRENT_BRANCH"
    echo ""
    echo -e "${GREEN}✓ Pushed to GitHub${NC}"
    echo ""
    echo "Release Please will:"
    echo "  1. Analyze your commits since the last release"
    echo "  2. Determine the next version number"
    echo "  3. Create a Release PR with updated CHANGELOG"
    echo "  4. When you merge the PR, it will create a GitHub release"
    echo ""
    echo -e "Check your GitHub repository for the Release PR!"
else
    echo -e "${YELLOW}Cancelled.${NC}"
fi
