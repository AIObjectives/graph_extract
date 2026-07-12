#!/usr/bin/env bash
set -e  # exit on error

ENV_NAME="annotatorconda"
PYTHON_VERSION="3.12.12"

# ── Conda env ────────────────────────────────────────────────────────────────
echo "Creating conda environment '$ENV_NAME'..."
conda create -y -n "$ENV_NAME" python="$PYTHON_VERSION"

# Activate (works in both bash and zsh when conda is initialized)
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

# ── nvm ──────────────────────────────────────────────────────────────────────
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Load nvm into the current shell session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# ── Node ─────────────────────────────────────────────────────────────────────
nvm install node
nvm use node

# ── npm packages ─────────────────────────────────────────────────────────────
npm install vis-network

# ── pip packages ─────────────────────────────────────────────────────────────
pip install \
  pandas \
  numpy \
  seaborn \
  matplotlib \
  scipy \
  requests \
  python-dotenv \
  typer \
  openai \
  jsonlines \
  statmodels

# This calls pyproject.toml, which means the root-level directory is is "editable" mode, so folders become visible from everywhere (apparently)
pip install -e .

echo "now run 'conda activate $ENV_NAME' to activate the environment."
