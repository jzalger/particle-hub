# particle-hub
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=jzalger_particle-hub&metric=bugs)](https://sonarcloud.io/dashboard?id=jzalger_particle-hub)

A data logging hub for the Particle IoT platform.

## Docker-compose reference
`docker-compose up` from project root directory.

## Docker Command reference
Build the image
`docker build -t particlehub:latest .`

Run the image:
`docker run -p80:5000 particlehub:latest`

Stopping all images
`docker ps -a -q | xargs docker rm`

Removing all images:
`docker images -a -q | xargs docker rmi -f`
