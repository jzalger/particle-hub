job "particlehub" {
  datacenters = ["dc1"]
  type = "service"

  update {
    stagger      = "30s"
    max_parallel = 2
  }

  group "particlehub" {
    # Specify the number of these tasks we want.
    count = 1

    network {
      port "http" {
        static = 5000
      }
    }

    service {
      name = "particlehub"
      port = "http"
      check {
        type     = "http"
        path     = "/"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "particlehub" {
      driver = "docker"

      config {
        image = "dockerhub-user/particlehub:latest"
        ports = ["http"]
        volumes = ["secrets/phconfig.py:/run/secrets/phconfig.py"]
        auth {
          username = "dockerhub-user"
          password = "dockerhub-password"
        }
      }
      template {
        data = <<EOF
        {{ with secret "kv/data/machine/dev/apps/particlehub" }}
        cloud_api_token = "{{ .Data.data.cloud_api_token }}"
        influx_db_name = "{{ .Data.data.influx_db_name }}"
        influx_user = "{{ .Data.data.influx_user }}"
        influx_password = "{{ .Data.data.influx_password }}"
        influx_host = "{{ .Data.data.influx_host }}"
        web_host = "{{ .Data.data.web_host }}"
        influx_port = {{ .Data.data.influx_port }}
        influx_credentials = dict(host=influx_host, port=influx_port, username=influx_user,
                                  password=influx_password, database=influx_db_name)
        log_config = dict(influx=influx_credentials)
        default_log_source = "{{ .Data.data.default_log_source }}"
        syslog_host = {{ .Data.data.syslog_host }}
        {{ end }}
        EOF
        destination = "secrets/phconfig.py"
      }
      resources {
        cpu    = 500 # MHz
        memory = 256 # MB
      }
      vault {
        policies = ["particlehub-dev"]
      }
    }
  }
}
