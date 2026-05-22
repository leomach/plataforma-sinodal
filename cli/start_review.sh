#!/bin/bash

# Ensure the script is run from the project root
if [ ! -f "manage.py" ]; then
    echo "Erro: Este script deve ser executado da raiz do projeto (onde o manage.py está)."
    exit 1
fi

command_exists() {
  type "$1" &>/dev/null
}

export GITHUB_REPO="leomach/plataforma-sinodal"
export GITHUB_USERNAME=$(cat ~/.githubrc 2>/dev/null | grep user.login | cut -d ":" -f2 | xargs)
export GITHUB_PASSWORD=$(cat ~/.githubrc 2>/dev/null | grep user.password | cut -d ":" -f2 | xargs)
export BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ -z "$GITHUB_USERNAME" ]; then
  read -p "Digite seu Github username: " GITHUB_USERNAME
  echo "user.login: $GITHUB_USERNAME" >>~/.githubrc
fi

if [ -z "$GITHUB_PASSWORD" ]; then
  read -p "Digite seu Github password (não será mostrado): " -s GITHUB_PASSWORD
  echo "user.password: $GITHUB_PASSWORD" >>~/.githubrc
fi

read -p "Deseja atualizar a versão antes do solicitar o review?
1. sim
2. não
" resp

if [[ $resp == "1" ]]; then
  source cli/update_version.sh
  git add .
  git commit -m "update version"
  git push origin $BRANCH
fi

# read -p "Digite o cod-nome da sua branch: " TASK
read -p "Digite o nome da branch que receberá esse review: " BASE

# export IN_PROGRESS_LABEL="Stage: In progress"
# export REVIEW_LABEL="Stage: Review"

# response=$(curl -u "$GITHUB_USERNAME:$GITHUB_PASSWORD" -sL "https://api.github.com/repos/$GITHUB_REPO/issues/$ISSUE_ID/labels/$IN_PROGRESS_LABEL" -X "DELETE")
# if [[ "$response" == *"errors"* ]]; then
#     echo "Error removing label"
# else
#     echo "Label $IN_PROGRESS_LABEL removed"
# fi

# response=$(curl -u "$GITHUB_USERNAME:$GITHUB_PASSWORD" -sL "https://api.github.com/repos/$GITHUB_REPO/issues/$ISSUE_ID/labels" -X "POST" -d "[\"$REVIEW_LABEL\"]")
# if [[ "$response" == *"errors"* ]]; then
#     echo "Error adding label"
# else
#     echo "Label $REVIEW_LABEL added"
# fi

pr_url=https://github.com/$GITHUB_REPO/compare/$BASE...$BRANCH?expand=1
if command_exists open; then
  open $pr_url
fi
if command_exists xdg-open; then
  xdg-open $pr_url
fi
