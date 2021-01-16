# particle-hub
[![Known Vulnerabilities](https://snyk.io/test/github/jzalger/particle-hub/badge.svg?targetFile=Dockerfile)](https://snyk.io/test/github/jzalger/particle-hub?targetFile=Dockerfile)

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
