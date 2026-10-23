#!/bin/sh
set -e

MODEL_NAME=${MODEL_NAME:-"Qwen/Qwen2.5-1.5B-Instruct"}
CACHE_DIR=${CACHE_DIR:-"/model-cache"}

echo "Проверка наличия модели в $CACHE_DIR..."
if [ -f "$CACHE_DIR/config.json" ]; then
    echo "Модель уже скачана. Пропускаю."
    exit 0
fi

echo "Скачивание модели $MODEL_NAME..."
pip install --no-cache-dir "huggingface_hub[cli]"
hf download "$MODEL_NAME" --local-dir "$CACHE_DIR"
echo "Скачивание завершено."
