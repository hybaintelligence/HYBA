#!/usr/bin/env bash

echo "=== Starting installation of development tools ==="

# Install NVM if not already installed
if [ ! -d "$HOME/.nvm" ]; then
  echo "--- Installing NVM ---"
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi

# Source NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Install Node.js 22
echo "--- Installing Node.js 22 ---"
nvm install 22
nvm alias default 22

echo "Node.js version:"
node --version
echo "npm version:"
npm --version

# Install pnpm
echo "--- Installing pnpm ---"
npm install -g pnpm
echo "pnpm version:"
pnpm --version

# Install pyenv if not already installed
if [ ! -d "$HOME/.pyenv" ]; then
  echo "--- Installing pyenv ---"
  git clone https://github.com/pyenv/pyenv.git "$HOME/.pyenv"
fi

# Set up pyenv in PATH
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

echo "pyenv version:"
pyenv --version

# Install Python 3.12
echo "--- Installing Python 3.12 ---"
pyenv install 3.12.7
pyenv global 3.12.7

echo "Python version:"
python --version
echo "pip version:"
pip --version

echo "=== Installation complete! ==="
