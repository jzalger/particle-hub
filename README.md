# particle-hub
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=jzalger_particle-hub&metric=bugs)](https://sonarcloud.io/dashboard?id=jzalger_particle-hub)
[![codecov](https://codecov.io/gh/jzalger/particle-hub/branch/master/graph/badge.svg?token=76Y8JQG9ZC)](https://codecov.io/gh/jzalger/particle-hub)

A data logging hub for the Particle IoT platform.

## Run using Docker container
```
git clone https://github.com/jzalger/particle-hub.git
cd particle-hub

# Edit phconfig template with Particle.IO and log database credentials
nano phconfig_template.py
mv phconfig_template.py phconfig.py

docker-compose up

# Service will run on port 5000 of the docker container
```