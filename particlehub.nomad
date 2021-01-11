job "particlehub" {
  datacenters = ["dc1"]
  type = "service"

  update {
    stagger      = "30s"
    max_parallel = 2
  }

  group "webservices" {
    # Specify the number of these tasks we want.
    count = 1

    network {
      port "http" {
        static = 5000
      }
    }

    service {
      port = "http"

      check {
        type     = "http"
        path     = "/"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "frontend" {
      driver = "docker"

      # Configuration is specific to each driver.
      config {
        image = "particlehub:latest"
      }

      env {
        DB_HOST = "db01.example.com"
      }

      # Specify the maximum resources required to run the task,
      # include CPU and memory.
      resources {
        cpu    = 500 # MHz
        memory = 256 # MB
      }
    }
  }
}