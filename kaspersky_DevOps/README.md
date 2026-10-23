# Тестовое задание | Intern DevOps Safeboard 2026

## Локальный отказоустойчивый контур мониторинга для Uptime Kuma

### 🧱 Архитектура
Проект состоит из двух независимых слоёв:
1. **Приложение:** Uptime Kuma + MariaDB (volume для сохранения данных).
2. **Наблюдаемость:** Prometheus + Grafana + экспортеры (cAdvisor, node-exporter, mysqld-exporter).

Вся инфраструктура управляется через **Dagger-модуль** (Python SDK), который взаимодействует с Docker через проброс сокета `/var/run/docker.sock`.

### ⚙️ Требования
* **Windows 10/11** с установленным **Docker Desktop**.
* **WSL 2** с дистрибутивом **Ubuntu**.
* **Dagger CLI** (устанавливается в WSL).
* **Python 3.12+** (в WSL).

### 🚀 Подготовка окружения

1. **Настройте Docker Desktop:**
   * Откройте Docker Desktop → **Settings** → **Resources** → **WSL Integration**.
   * Включите интеграцию с вашим дистрибутивом **Ubuntu**.
   * Нажмите **Apply & Restart**.

2. **Установите Dagger CLI в WSL (Ubuntu):**
   Откройте терминал Ubuntu и выполните:
   ```bash
   curl -fsSL https://dl.dagger.io/dagger/install.sh | BIN_DIR=$HOME/.local/bin sh
   echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   dagger version
   ```

### 📂 Запуск проекта

1. Перейдите в папку проекта (внутри WSL):
   ```bash
   cd ~/kaspersky_DevOps
   ```

2. **Запустите приложение (Uptime Kuma + MariaDB):**
   ```bash
   dagger call deploy-app --docker-sock /var/run/docker.sock --app-dir ./app
   ```

3. **Запустите мониторинг (Prometheus + Grafana):**
   ```bash
   dagger call deploy-monitoring --docker-sock /var/run/docker.sock --monitoring-dir ./monitoring
   ```

4. **Настройте Grafana (Data Source + дашборд):**
   ```bash
   dagger call configure-grafana --dashboard-file ./grafana-dashboard.json
   ```

5. **Бонус: End-to-End Orchestration (всё одной командой):**
   ```bash
   dagger call deploy-all \
     --docker-sock /var/run/docker.sock \
     --app-dir ./app \
     --monitoring-dir ./monitoring \
     --dashboard-file ./grafana-dashboard.json
   ```
   В случае успеха вы увидите `ALL SYSTEMS UP`.

### 🌐 Доступ к сервисам
* **Uptime Kuma:** http://localhost:3001
* **Grafana:** http://localhost:3000 (логин: `admin`, пароль: `admin`)
* **Prometheus:** http://localhost:9090

### ✅ Проверка работоспособности
1. Откройте Uptime Kuma и убедитесь, что сервис доступен (например, добавьте монитор на `http://localhost:3000` и проверьте, что он зелёный).
2. Откройте Grafana → **Dashboards** → **Kaspersky DevOps Monitoring**. Должны отображаться панели:
   * CPU Usage (containers)
   * Memory Usage (containers)
   * MariaDB Status
   * Uptime Kuma Status

### 📁 Структура проекта
```
.
├── app/                          # docker-compose.yml для Uptime Kuma + MariaDB
├── monitoring/                   # docker-compose.yml для Prometheus + Grafana
├── config/
│   ├── prometheus/               # prometheus.yml (резервная копия)
│   └── grafana/                  # (опционально) provisioning
├── grafana-dashboard.json        # JSON-модель дашборда
├── src/kaspersky_dev_ops/main.py # Dagger-модуль на Python
├── prometheus.yml                # Конфиг Prometheus
├── mysql-exporter.cnf            # Конфиг mysqld-exporter
└── README.md
```