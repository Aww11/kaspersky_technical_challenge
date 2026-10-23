# vLLM on Kubernetes (kind) — Тестовое задание

## Компоненты
- **vLLM (CPU)**: инференс модели `Qwen2.5-1.5B-Instruct`.
- **Rootless Docker-образ**: сборка из `docker/Dockerfile.vllm`.
- **InitContainer**: скачивание модели в PVC (`docker/Dockerfile.downloader`).
- **K8s-манифесты**: `k8s/base/` + Kustomize (`k8s/overlays/dev/`).
- **Скрипты**: `scripts/download_model.sh` (загрузка), `scripts/load_test.py` (нагрузочный тест).

## Требования
- Docker Desktop с включенным Kubernetes (kind).
- `kubectl`, `kind` (в WSL).

## Запуск
1. Соберите образы:
   ```bash
   docker build -f docker/Dockerfile.vllm -t my-vllm-cpu:latest .
   docker build -f docker/Dockerfile.downloader -t my-model-downloader:latest .
   ```
2. Загрузите их в кластер:
   ```bash
   kind load docker-image my-vllm-cpu:latest --name desktop
   kind load docker-image my-model-downloader:latest --name desktop
   ```
3. Разверните через Kustomize:
   ```bash
   kubectl apply -k k8s/overlays/dev
   ```
4. Дождитесь запуска пода:
   ```bash
   kubectl get pods -n vllm -w
   ```

## Проверка API
### Способ 1: Через `port-forward`
В первом терминале:
```bash
kubectl port-forward -n vllm svc/vllm-service 8000:8000
```
Во втором терминале:
```bash

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 1234" \
  -d '{"model": "/model-cache", "messages": [{"role": "user", "content": "Привет!"}], "max_tokens": 20}'
```
### Способ 2:
```bash
kubectl run -n vllm curl-test --rm -i --tty --image=curlimages/curl --restart=Never -- \
  curl -X POST http://vllm-service:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 1234" \
  -d '{"model": "/model-cache", "messages": [{"role": "user", "content": "Привет!"}], "max_tokens": 20}'
```

## Нагрузочный тест
1. Запустите временный под:
   ```bash
   kubectl run -n vllm load-test --rm -i --tty --image=python:3.12-slim --restart=Never -- bash
   ```
2. Внутри пода:
   ```bash
   pip install requests
   cat > /tmp/load_test.py << 'PYEOF'
   # (код из scripts/load_test.py)
   PYEOF
   python3 /tmp/load_test.py
   ```

### Результаты (CPU, 1.5B)
| Промпт | TTFT (s) | Latency (s) | Throughput (tok/s) |
|--------|----------|-------------|---------------------|
| Короткий (1-й) | 0.20 | 54.85 | 0.38 |
| Короткий (2-й) | 0.34 | 2.46 | 8.52 |
| Длинный (1-й) | 0.50 | 2.74 | 7.66 |

**Аналитика:**
- **А) Много коротких запросов:** увеличить `--max-num-seqs`, `VLLM_CPU_KVCACHE_SPACE`.
- **Б) Длинный контекст:** увеличить `--max-model-len`, включить `--enable-chunked-prefill`.

## 📝 Примечание
Если `kind load` не работает, используйте `docker save` + `docker cp` + `ctr import` (см. комментарии в проекте).