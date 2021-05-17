killall webservice.py
killall dead_drop.py
killall python3

nohup epcis_sanitiser/webservice.py -p 8080 -r -H 0.0.0.0 -l DEBUG -d https://discovery.epcat.de/dead_drop >> ~/discovery_service.log 2>&1 &
nohup dead_drop/dead_drop.py -p 8090 -R "/dead_drop" -r -H 0.0.0.0 -l DEBUG >> ~/dead_drop.log 2>&1 &
