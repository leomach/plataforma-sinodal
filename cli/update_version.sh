#!/bin/bash

# Determine the location of version.py
if [ -f "setup/version.py" ]; then
  VERSION_FILE="setup/version.py"
elif [ -f "../setup/version.py" ]; then
  VERSION_FILE="../setup/version.py"
else
  echo "Erro: setup/version.py não encontrado."
  exit 1
fi

# Ler a versão atual do arquivo
# Grep for VERSION="x.y.z" or VERSION = "x.y.z"
CURRENT_VERSION_LINE=$(grep -E 'VERSION *= *".*"' "$VERSION_FILE")
# Extract the version number inside quotes
VERSION=$(echo "$CURRENT_VERSION_LINE" | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$VERSION" ]; then
  echo "Erro: Não foi possível ler a versão em $VERSION_FILE"
  exit 1
fi

# Separar a versão em componentes major, minor e patch
IFS='.' read -r major minor patch <<<"$VERSION"

# Pedir ao usuário qual parte da versão eles querem atualizar
echo "Versão atual: $VERSION"
read -p "Qual parte da versão você deseja atualizar?
1. major
2. minor
3. patch
" part

# Atualizar a versão de acordo com a escolha do usuário
case $part in
1)
  ((major++))
  minor=0 # Reset minor version to 0
  patch=0 # Reset patch version to 0
  ;;
2)
  ((minor++))
  patch=0 # Reset patch version to 0
  ;;
3)
  ((patch++))
  ;;
*)
  echo "Opção invalida. Por favor digite 1 para major, 2 para minor ou 3 para patch."
  exit 1
  ;;
esac

# Atualizar a versão
new_version=$major.$minor.$patch

# Escrever a nova versão de volta no arquivo
# Using -i.bak for compatibility (macOS requires extension with -i)
sed -i.bak -E "s/(VERSION *= *\")[^\"]*(\")/\1$new_version\2/" "$VERSION_FILE"

# Remove backup file
rm -f "${VERSION_FILE}.bak"

# Exibir mensagem de sucesso
echo "Versão do projeto atualizada para $new_version"
