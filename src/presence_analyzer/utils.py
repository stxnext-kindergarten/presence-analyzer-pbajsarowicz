# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
from json import dumps
from functools import wraps
from datetime import datetime
from flask import Response
from presence_analyzer.main import app
import logging
log = logging.getLogger(__name__)  # pylint: disable=C0103
from lxml import etree
import urllib2
import threading
import time
from collections import OrderedDict
import locale
CACHE = {}


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped
    function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):  # pylint: disable=C0111
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


def get_data_from_xml():
    """
    Extracts data from XML file and groups it by user_id.

    It creates structure like this:
    data = {
        141: {
            'avatar': '/api/images/users/141',
            'name': 'Adam P.'
        },
        176: {
            'avatar': '/api/images/users/176',
            'name': 'Adrian K.'
        },
    }
    """
    data = {}
    with open(app.config['DATA_XML'], 'r') as xmlfile:
        tree = etree.parse(xmlfile)
        server = tree.find("server")
        host = server.find("host").text
        port = server.find("port").text
        protocol = server.find("protocol").text
        users_node = tree.find("users")
        users = users_node.findall("user")
        for user in users:
            avatar = user.find("avatar").text
            name = user.find("name").text
            user_id = user.get("id")
            data.setdefault(int(user_id), {
                'avatar': '{}://{}:{}{}'.format(protocol, host, port, avatar),
                'name': name
            })
    locale.setlocale(locale.LC_ALL, "pl_PL.UTF-8")
    sorted_data = OrderedDict(
        sorted(data.items(), key=lambda(k, v): (v['name']), cmp=locale.strcoll)
    )
    return sorted_data


def update_data_from_xml():
    """
    Update xml file
    """
    with open(app.config['DATA_XML'], 'w') as xmlfile:
        data = urllib2.urlopen(app.config['DATA_XML_URL'])
        temp = data.read()
        xmlfile.write(temp)


def locker(func):
    """
    Lock thread when missing
    """
    func.lock = threading.Lock()

    def wrap(*args, **kwargs):
        """
        Call acquire() method when block is entered,
        release() when exited
        """
        with func.lock:
            return func(*args, **kwargs)
    return wrap


def cache(key, expiration_time):
    """
    Cache for data from CSV file.
    """
    def wrap(func):
        def wrap_cache(*args, **kwargs):
            if key in CACHE and time.time() - CACHE[key]['time']:
                    return CACHE[key]['data']
            CACHE[key] = {
                'data': func(*args, **kwargs),
                'time': time.time()
            }
            return CACHE[key]['data']
        return wrap_cache
    return wrap


@locker
@cache('cache', 200)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue
            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {
                'start': start,
                'end': end
            }
    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def return_id_start_end(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: {'start': [], 'end': []} for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(seconds_since_midnight(start))
        result[date.weekday()]['end'].append(seconds_since_midnight(end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
