# Installation
This charm requires a Redis datastore. Not the one in the charmstore is used, but the one written by James Beedy (https://github.com/jamesbeedy/juju-charm-redis). This repo must be cloned and then build using charm build.
assuming in the directory above the cloned repo:
```
charm build -s xenial juju-charm-redis
```
From the directory housing the builded charms:
```
juju deploy ./redis
```
Installing RabbitMQ and Sensu-base:
```
juju deploy rabbitmq-server
juju deploy sensu-base
```
Sensu provides it's own tool to generate all the required SSL-certificates, which are valid for 5 years. More info can be found here https://sensuapp.org/docs/latest/reference/ssl.html. Short version:
```
wget http://sensuapp.org/docs/0.29/files/sensu_ssl_tool.tar
tar -xvf sensu_ssl_tool.tar
cd sensu_ssl_tool
./ssl_certs.sh generate
```
Executing the following command will parse all the correct ssl settings to rabbitmq.
It assumes you are in the sensu_ssl_tool dir.
```
juju config rabbitmq-server ssl_key="`cat server/key.pem`" ssl_cert="`cat server/cert.pem`" ssl_ca="`cat sensu_ca/cacert.pem`" ssl_enabled=True
```
Then connect the services:
```
juju add-relation redis sensu-base
juju add-relation rabbitmq-server sensu-base
```
When Sensu-base is complety setup, the rabbitmq-server password will be visible in its status message (of the Sensu-base). This password is needed as a config value for the Sensu clients.

# Remarks
Only one Sensu-base is needed to monitor all the services in a controller. The sensu-client just need the private ip, port and ssl-data of the RabbitMQ. For now this is given through config options, but when cross-model relations become available, this should be rewritten using a relation.

# Bugs
Report bugs on <a href="https://github.com/Qrama/monitoring-api/issues">Github</a>

# Author
Mathijs Moerman <a href="mailto:mathijs.moerman@tengu.io">mathijs.moerman@tengu.io</a>
