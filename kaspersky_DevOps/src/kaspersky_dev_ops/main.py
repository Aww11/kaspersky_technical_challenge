import dagger
from dagger import dag, function, object_type

@object_type
class KasperskyDevOps:
    @function
    async def deploy_app(
        self, 
        docker_sock: dagger.Socket, 
        app_dir: dagger.Directory
    ) -> str:
        """Поднимает MariaDB и Uptime Kuma"""
        return await (
            dag.container()
            .from_("docker:cli")
            .with_unix_socket("/var/run/docker.sock", docker_sock)
            .with_directory("/app", app_dir)
            .with_workdir("/app")
            .with_exec(["docker", "compose", "up", "-d"])
            .stdout()
        )

    @function
    async def deploy_monitoring(
        self, 
        docker_sock: dagger.Socket, 
        monitoring_dir: dagger.Directory
    ) -> str:
        """Поднимает Prometheus и Grafana"""
        return await (
            dag.container()
            .from_("docker:cli")
            .with_unix_socket("/var/run/docker.sock", docker_sock)
            .with_directory("/monitoring", monitoring_dir)
            .with_workdir("/monitoring")
            .with_exec(["docker", "compose", "up", "-d"])
            .stdout()
        )

    @function
    async def configure_grafana(self, dashboard_file: dagger.File) -> str:
        """Настраивает Data Source и дашборд в Grafana через API"""
        ctr = (
            dag.container()
            .from_("alpine:latest")
            .with_exec(["apk", "add", "curl"])
            .with_mounted_file("/dashboard.json", dashboard_file)
            .with_exec([
                "sh", "-c",
                "sleep 5 && "
                "curl -s -X POST http://host.docker.internal:3000/api/datasources "
                "-H 'Content-Type: application/json' "
                "-u admin:admin "
                "-d '{\"name\":\"Prometheus\",\"type\":\"prometheus\",\"url\":\"http://prometheus:9090\",\"access\":\"proxy\",\"isDefault\":true}' && "
                "curl -s -X POST http://host.docker.internal:3000/api/dashboards/import "
                "-H 'Content-Type: application/json' "
                "-u admin:admin "
                "--data-binary @/dashboard.json"
            ])
        )
        return await ctr.stdout()

    @function
    async def deploy_all(
        self,
        docker_sock: dagger.Socket,
        app_dir: dagger.Directory,
        monitoring_dir: dagger.Directory,
        dashboard_file: dagger.File
    ) -> str:
        """Поднимает всю платформу и валидирует статус систем"""
        # 1. Поднимаем приложение
        await self.deploy_app(docker_sock, app_dir)
        
        # 2. Поднимаем мониторинг
        await self.deploy_monitoring(docker_sock, monitoring_dir)
        
        # 3. Настраиваем Grafana
        await self.configure_grafana(dashboard_file)
        
        # 4. Валидация: проверяем, что все контейнеры запущены
        validation = await (
            dag.container()
            .from_("docker:cli")
            .with_unix_socket("/var/run/docker.sock", docker_sock)
            .with_exec([
                "sh", "-c",
                # Ждем 10 секунд, чтобы все контейнеры успели подняться
                "sleep 10 && "
                # Проверяем, что нужные контейнеры в статусе Up
                "for c in uptime-kuma kuma-db prometheus grafana cadvisor node-exporter mysqld-exporter; do "
                "  status=$(docker inspect -f '{{.State.Status}}' $c 2>/dev/null); "
                "  if [ \"$status\" != \"running\" ]; then echo \"FAIL: $c is $status\"; exit 1; fi; "
                "done && echo 'ALL SYSTEMS UP'"
            ])
            .stdout()
        )
        return validation
