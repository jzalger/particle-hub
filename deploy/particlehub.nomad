job "particlehub" {
  datacenters = ["dc1"]
  type = "service"

  group "particlehub" {
    # Specify the number of these tasks we want.
    count = 1

    network {
      port "https" {
        static = 5000
      }
    }

    service {
      name = "particlehub"
      tags = ["particlehub", "webservice", "tls", "vault"]
      port = "https"
      check {
        type     = "http"
        protocol = "https"
        path     = "/"
        interval = "60s"
        timeout  = "10s"
        tls_skip_verify = true
      }
    }

    task "particlehub" {
      driver = "docker"

      env {
        PHCONFIG_FILE = "/run/secrets/phconfig.py"
      }

      config {
        image = "jzalger/particlehub:latest"
        ports = ["https"]
        volumes = ["secrets:/run/secrets"]
      }

      template {
        data = <<EOF
{{ with secret "pki_int/issue/app-certificates" "common_name=particlehub" "ttl=96h"}}
{{ .Data.private_key }}
{{ end }}
EOF
        destination = "secrets/particlehub.key"
      }

      template {
        data = <<EOF
{{ with secret "pki_int/issue/app-certificates" "common_name=particlehub" "ttl=96h"}}
{{ .Data.certificate }}
{{ end }}
EOF
        destination = "secrets/particlehub.crt"
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
influx_credentials = dict(host=influx_host, port=influx_port, username=influx_user, password=influx_password, database=influx_db_name)
log_config = dict(influx=influx_credentials)
default_log_source = "{{ .Data.data.default_log_source }}"
syslog_host = {{ .Data.data.syslog_host }}
{{ end }}
EOF
        destination = "secrets/phconfig.py"
      }
      resources {
        cpu    = 1024 # MHz
        memory = 300 # MB
      }
      vault {
        policies = ["particlehub-dev"]
      }
    }
  }
}
