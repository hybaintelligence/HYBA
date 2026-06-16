#!/bin/bash

# First fix the PATH
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

echo "=== Fixed PATH: $PATH ==="

# Now let's install NVM if not present
if [ ! -d "$HOME/.nvm" ]; then
  echo "Cloning NVM..."
  git clone https://github.com/nvm-sh/nvm.git "$HOME/.nvm"
  cd "$HOME/.nvm"
  git checkout v0.40.1
  cd -
else
  echo "NVM already cloned"
fi

# Now install Node.js with NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

echo "=== NVM loaded, installing Node.js 22 ==="
nvm install 22
nvm alias default 22

# Now handle pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

echo "=== pyenv loaded, installing Python 3.12 ==="
pyenv install 3.12.7
pyenv global 3.12.7

echo "=== Done! ==="
