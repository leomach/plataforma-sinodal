#!/bin/bash

export GITHUB_REPO="leomach/plataforma-sinodal"
export GITHUB_USERNAME=$(cat ~/.githubrc 2>/dev/null | grep user.login | cut -d ":" -f2 | xargs)
export GITHUB_PASSWORD=$(cat ~/.githubrc 2>/dev/null | grep user.password | cut -d ":" -f2 | xargs)

if [ -z "$GITHUB_USERNAME" ]; then
  read -p "Digite seu Github username: " GITHUB_USERNAME
  echo "user.login: $GITHUB_USERNAME" >>~/.githubrc
fi

if [ -z "$GITHUB_PASSWORD" ]; then
  read -p "Digite seu Github password (não será mostrado): " -s GITHUB_PASSWORD
  echo "user.password: $GITHUB_PASSWORD" >>~/.githubrc
fi

read -p "Digite o name-id da tarefa (será criada uma branch com esse nome): " TASK
read -p "Digite o name-id da branch de origem (a branch será atualizada antes do checkout): " BRANCH

git checkout $BRANCH
git pull origin $BRANCH
git checkout -b $TASK

# export LABEL="Stage: In progress"

# response=$(curl -u "$GITHUB_USERNAME:$GITHUB_PASSWORD" -sL "https://api.github.com/repos/$GITHUB_REPO/issues/$ISSUE_ID/labels" -X "POST" -d "[\"$LABEL\"]")
# if [[ "$response" == *"errors"* ]]; then
#     echo "Error adding label"
# else
#     echo "Label $LABEL added"
# fi

# response=$(curl -u "$GITHUB_USERNAME:$GITHUB_PASSWORD" -sL "https://api.github.com/repos/$GITHUB_REPO/issues/$ISSUE_ID/assignees" -X "POST" -d "{\"assignees\": [\"$GITHUB_USERNAME\"]}")
# if [[ "$response" == *"errors"* ]]; then
#     echo "Error adding label"
# else
#     echo "$GITHUB_USERNAME assigned to issue"
# fi
