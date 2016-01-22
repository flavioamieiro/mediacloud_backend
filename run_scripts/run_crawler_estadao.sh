#!/bin/bash

source /srv/mediacloud/mediacloud_backend/bin/activate
cd /srv/mediacloud/mediacloud_backend/mediacloud_backend/capture

python crawler_estadao.py politica 1
python crawler_estadao.py economia 1
python crawler_estadao.py internacional 1
python crawler_estadao.py esportes 1
python crawler_estadao.py sao-paulo 1
python crawler_estadao.py cultura 1
python crawler_estadao.py opiniao 1
python crawler_estadao.py alias 1
python crawler_estadao.py brasil 1
python crawler_estadao.py ciencia 1
python crawler_estadao.py educacao 1
python crawler_estadao.py saude 1
python crawler_estadao.py sustentabilidade 1
python crawler_estadao.py viagem 1
