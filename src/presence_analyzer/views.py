# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, url_for
from flask import Flask
from flask.ext.mako import MakoTemplates, render_template, exceptions
app = Flask(__name__)  # pylint: disable-msg=C0103
mako = MakoTemplates(app)  # pylint: disable-msg=C0103
from presence_analyzer.main import app
from presence_analyzer.utils import jsonify, get_data, mean, group_by_weekday
from presence_analyzer.utils import return_id_start_end, get_data_from_xml

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

pages_list = [
    'presence_weekday',
    'mean_time_weekday',
    'presence_start_end'
]


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for('page_to_render', page_name='presence_weekday'))


@app.route('/<string:page_name>', methods=['GET'])
def page_to_render(page_name):
    """
    Returns name of page to render
    """
    try:
        if page_name not in pages_list:
            raise exceptions.TopLevelLookupException(page_name)
        else:
            return render_template('{}.html'.format(page_name))
    except exceptions.TopLevelLookupException:
        return render_template('{}.html'.format('page_not_found'))
    return render_template('{}.html'.format(page_name))


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data_xml = get_data_from_xml()
    return [{
        'user_id': user_id,
        'avatar': details['avatar'],
        'name': details['name']
    } for user_id, details in data_xml.iteritems()]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns interval presence time
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = return_id_start_end(data[user_id])
    result = [(calendar.day_abbr[key],
               mean(value['start']),
               mean(value['end']))
              for key, value in weekdays.items()]

    return result
