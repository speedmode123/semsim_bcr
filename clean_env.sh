#!/bin/bash

docker stop $(docker ps -aq)
docker remove $(docker ps -aq)
docker rmi -f $(docker images -aq)

# if [ docker ps -aq ]; then
#   docker stop $(docker ps -aq)
# fi
# if [ docker images -aq ]; then 
#   docker rmi -f $(docker images -aq)
# fi
# if [ docker images -aq ]; then 
#    docker remove $(docker images -aq)
# fi
