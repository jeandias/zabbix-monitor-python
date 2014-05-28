import os, sys
import bottle
import json
import locale
from bottle import route, response, request
from datetime import datetime
from operator import itemgetter
from zabbix_api import ZabbixAPI

locale.setlocale(locale.LC_TIME, "pt_BR.utf8")

PRIORITY_CLASS = {
  5: u'disaster',
  4: u'high',
  3: u'average',
  2: u'warning',
  1: u'information',
  0: u'not_classified'
}

# connect to Zabbix API
zapi = ZabbixAPI(server="http://localhost", path="", log_level=0)
zapi.login("user", "password")

@route('/')
def index():
    response.content_type = 'application/json'

    # Retrieve host groups
    hostgroups = zapi.hostgroup.get({})

    # Retrieve hosts
    hosts = zapi.host.get({
        "groupids": [g['groupid'] for g in hostgroups],
        "output": ["hostid","host"]
        })

    # Retrieve triggers
    triggers = zapi.trigger.get({
        "hostids": [h['hostid'] for h in hosts],
        "output": "extend",
        "filter": {"value": 1},
        "sortfield": ["lastchange", "priority"],
        "sortorder": "DESC",
        "skipDependent": True,
        "expandDescription": True,
        "withUnacknowledgedEvents": True,
        "monitored": True
        })

    issues = []
    for trigger in triggers:
        issue = dict(
            host = hosts[map(itemgetter('hostid'), hosts).index(trigger["hostid"])]["host"],
            description = trigger["description"],
            lastchange = datetime.fromtimestamp(int(trigger["lastchange"])).strftime('%d %b %Y %H:%M:%S'),
            age = datetime.fromtimestamp(int(trigger["lastchange"])).strftime('%Y%m%d%H%M%S'),
            priority = PRIORITY_CLASS[int(trigger["priority"])]
        )
        issues.append(issue)

    return json.dumps(issues, indent=4)


application = bottle.default_app()
