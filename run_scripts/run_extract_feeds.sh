#!/bin/bash

source /srv/mediacloud/mediacloud_backend/bin/activate
cd /srv/mediacloud/mediacloud_backend/mediacloud_backend/capture
python extract_feeds.py -d1
