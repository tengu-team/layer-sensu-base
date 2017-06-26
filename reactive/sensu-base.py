#!/usr/bin/env python3
# Copyright (C) 2017  Qrama, developed by Tengu-team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=c0111,c0103,c0301
import os
from charmhelpers.core.templating import render
from charmhelpers.core.hookenv import status_set, config, application_version_set, unit_private_ip
from charmhelpers.core.host import service_restart

from charms.reactive import when, when_not, set_state, remove_state


CONFIG_DIR = '/etc/sensu/conf.d'
SSL_DIR = '/etc/sensu/ssl'


@when('apt.installed.sensu')
@when_not('sensu.running', 'redis.connected', 'rabbitmq.connected')
def setup_sensu():
    application_version_set('0.29.0')
    status_set('blocked', 'Waiting for relation with RabbitMQ and Redis')


@when('rabbitmq.connected')
@when_not('rabbitmq.available')
def get_access_rabbitmq(rabbitmq):
    rabbitmq.request_access('sensu', '/sensu')
    status_set('waiting', 'Waiting on RabbitMQ to configure vhost')


@when('rabbitmq.available')
def configure_rabbitmq(rabbitmq):
    if not os.path.isdir(SSL_DIR):
        os.mkdir(SSL_DIR)
    with open('{}/ssl_key.pem'.format(SSL_DIR), 'w+') as ssl_key:
        ssl_key.write(config()['ssl_key'])
    with open('{}/ssl_cert.pem'.format(SSL_DIR), 'w+') as ssl_cert:
        ssl_cert.write(config()['ssl_cert'])
    data = {
        'username': rabbitmq.username(),
        'password': rabbitmq.password(),
        'vhost': rabbitmq.vhost(),
        'host': rabbitmq.private_address()
    }
    port = rabbitmq.ssl_port()
    if port is None:
        port = 5672
    else:
        data['ssl_key'] = '{}/ssl_key.pem'.format(SSL_DIR)
        data['ssl_cert'] = '{}/ssl_cert.pem'.format(SSL_DIR)
    data['port'] = port
    render('rabbitmq.json', '{}/rabbitmq.json'.format(CONFIG_DIR), context=data)


@when('redis.available')
@when_not('sensu.running', 'redis.setup')
def configure_redis(redis):
    data = redis.redis_data()
    render('redis.json', '{}/redis.json'.format(CONFIG_DIR), context=data)
    set_state('redis.setup')


@when('redis.available', 'rabbitmq.available')
@when_not('sensu.running')
def starting_sensu(redis, rabbitmq):
    render('transport.json', '{}/transport.json'.format(CONFIG_DIR), context={})
    service_restart('sensu-server')
    status_set('active', 'RabbitMQ (password: {}) and Redis'.format(rabbitmq.password()))
    set_state('sensu.running')


@when('sensu.running', 'api.available')
def setup_api(api):
    render('api.json', '{}/api.json'.format(CONFIG_DIR), context={'host': unit_private_ip(), 'port': 4567})
    service_restart('sensu-api')
    api.configure(4567)


@when('redis.available')
@when_not('rabbitmq.connected')
def missing_rabbitmq(redis):
    status_set('blocked', 'Waiting for relation with RabbitMQ')
    remove_state('sensu.running')


@when('rabbitmq.available')
@when_not('redis.connected')
def missing_redis(rabbitmq):
    status_set('blocked', 'Waiting for relation with Redis')
    remove_state('sensu.running')
    remove_state('redis.configured')


@when('redis.connected')
@when_not('redis.available')
def waiting_redis(redis):
    status_set('blocked', 'Waiting for Redis info')
