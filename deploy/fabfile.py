#-*- coding: utf-8 -*-
import os
import random

from fabric.api import cd, run, sudo, settings, prompt, prefix, local, env
from fabric.contrib.files import exists

USER = "mediacloud"
HOME = "/srv/mediacloud/"
LOG_DIR = os.path.join(HOME, "logs/")
PROJECT_ROOT = os.path.join(HOME, "mediacloud_backend/")
CODE_DIR = os.path.join(PROJECT_ROOT, "mediacloud_backend/")

ACTIVATE_SCRIPT = os.path.join(PROJECT_ROOT, "bin/activate")

REPOSITORY_URL = "https://github.com/NAMD/mediacloud_backend.git"


def _configure_twitter_capture():
    #TODO: configure monit to monitor twitter capture
    twitter_key_file_path = os.path.join(HOME, ".twitter_keys")
    if not exists(twitter_key_file_path):
        access_token_key = prompt("access token key:")
        access_token_secret = prompt("access token secret:")
        consumer_key = prompt("access token key:")
        consumer_secret = prompt("access token secret:")

        twitter_keys = "{}\n{}\n{}\n{}".format(access_token_key, access_token_secret,
                consumer_key, consumer_secret)

        sudo("echo '{}' > {}".format(twitter_keys, twitter_key_file_path))
        sudo('chown {0}:{0} {1}'.format(USER, twitter_key_file_path))
        sudo('chmod 600 {1}'.format(USER, twitter_key_file_path))

    config_file_path = os.path.join(CODE_DIR,
                "deploy/config/twitter_capture.conf")
    sudo("ln -sf {} /etc/supervisor/conf.d/".format(config_file_path))
    sudo("service supervisor restart")

def _update_code(rev):
    with cd(CODE_DIR):
        run("git remote update")
        run("git checkout {}".format(rev))
        run("git reset --hard {}".format(rev))

def _clone_repo(rev):
    run("git clone {} {}".format(REPOSITORY_URL, CODE_DIR))
    _update_code(rev)

def _create_database_config():
    database_config_file_path = os.path.join(HOME, ".mediacloud_database")
    if not exists(database_config_file_path):
        database_host = prompt("database host:", default="dirrj.pypln.org")
        sudo("echo '{}' > {}".format(database_host, database_config_file_path))
        sudo('chown {0}:{0} {1}'.format(USER, database_config_file_path))

def _update_repository(rev):
    run("git remote update")
    run("git checkout {}".format(rev))
    run("git reset --hard {}".format(rev))

def update_crontab():
    crontab_file = os.path.join(CODE_DIR, "deploy/config/mediacloud.crontab")
    with settings(user=USER):
        run('crontab {}'.format(crontab_file))

def create_deploy_user():
    with settings(warn_only=True):
        user_does_not_exist = run("id {}".format(USER)).failed

    if user_does_not_exist:
        sudo("useradd --shell=/bin/bash --home {} --create-home {}".format(
            HOME, USER))
        sudo("mkdir {}".format(LOG_DIR))
        sudo("chown -R {0}:{0} {1}".format(USER, LOG_DIR))
        sudo("mkdir {}".format(PROJECT_ROOT))
        sudo("chown -R {0}:{0} {1}".format(USER, PROJECT_ROOT))
        sudo("passwd {}".format(USER))
        existing_keys_path = os.path.join("~{0}".format(env.user), '.ssh/authorized_keys')
        new_keys_path = os.path.join("~{0}".format(USER), '.ssh/authorized_keys')
        sudo("mkdir {0}".format(os.path.dirname(new_keys_path)))
        sudo("cp {0} {1}".format(existing_keys_path, new_keys_path))
        sudo("chown -R {0}:{0} {1}".format(USER,
            os.path.dirname(new_keys_path)))
        _create_database_config()

def install_system_packages():
    packages = " ".join(["python-setuptools", "python-pip",
        "python-virtualenv", "python-dev", "build-essential", "supervisor",
        "git", "libxml2-dev", "libxslt1-dev", "libjpeg-dev", "zlib1g-dev"])
    sudo("apt-get update")
    sudo("apt-get install -y {}".format(packages))


def initial_setup(rev=None):
    if rev is None:
        rev = local("git rev-parse HEAD")
    install_system_packages()
    create_deploy_user()

    with settings(warn_only=True, user=USER):
        _clone_repo(rev)
        run("virtualenv {}".format(PROJECT_ROOT))

    _configure_twitter_capture()

def deploy(rev=None):
    if rev is None:
        rev = local("git rev-parse HEAD")

    with prefix("source {}".format(ACTIVATE_SCRIPT)), settings(user=USER), cd(PROJECT_ROOT):
        with cd(CODE_DIR):
            _update_code(rev)
            run("pip install -r requirements.txt")

    update_crontab()
    sudo("supervisorctl reload")
