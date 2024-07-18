#! /bin/bash
sudo docker compose -f docker-compose.local.yml run --rm django coverage run -m pytest
