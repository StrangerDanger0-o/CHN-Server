import requests
from flask import current_app as app, url_for
from mhn.ui import constants
from config import MHN_SERVER_HOME
import os
from werkzeug.contrib.cache import SimpleCache
import socket
import struct
from mhn.api.models import Sensor

flag_cache = SimpleCache(threshold=1000, default_timeout=300)
country_cache = SimpleCache(threshold=1000, default_timeout=300)
sensor_cache = SimpleCache(threshold=1000, default_timeout=300)


def is_RFC1918_addr(ip):
    # 10.0.0.0 = 167772160
    # 172.16.0.0 = 2886729728
    # 192.168.0.0 = 3232235520
    RFC1918_net_bits = ((167772160, 8), (2886729728, 12), (3232235520, 16))

    try:
        # ip to decimal
        ip = struct.unpack("!L", socket.inet_aton(ip))[0]

        for net, mask_bits in RFC1918_net_bits:
            ip_masked = ip & (2 ** 32 - 1 << (32 - mask_bits))
            if ip_masked == net:
                return True
    except Exception as e:
        print 'Error ({}) on is_RFC1918_addr: {}'.format(e, ip)

    return False


def get_flag_ip(ipaddr):
    if is_RFC1918_addr(ipaddr):
        return url_for('static', filename=constants.DEFAULT_FLAG_URL)

    flag = flag_cache.get(ipaddr)
    if not flag:
        flag = _get_flag_ip(ipaddr)
        flag_cache.set(ipaddr, flag)
    return flag


def get_country_ip(ipaddr):
    if is_RFC1918_addr(ipaddr):
        return constants.DEFAULT_COUNTRY_NAME

    name = country_cache.get(ipaddr)
    if not name:
        name = _get_country_ip(ipaddr)
        country_cache.set(ipaddr, name)
    return name

  
def get_sensor_name(sensor_id):
    sensor_name = sensor_cache.get(sensor_id)
    if not sensor_name:
        for s in Sensor.query:
            if s.uuid == sensor_id:
                sensor_name = s.hostname
                sensor_cache.set(sensor_id, sensor_name)
                break
    print 'Name: %s' % sensor_name
    return sensor_name


def _get_flag_ip(ipaddr):
    """
    Returns an address where the flag is located.
    Defaults to static immge: '/static/img/unknown.png'
    """
    flag_path = url_for(
        'static', filename='img/flags-iso/shiny/64') + '/{}.png'
    geo_api = 'https://api.ipgeolocationapi.com/geolocate/{}'
    try:
        # Using threatstream's geospray API to get
        # the country code for this IP address.
        r = requests.get(geo_api.format(ipaddr))
        ccode = r.json()['un_locode']
	app.logger.warning(r.json())
    except Exception:
        app.logger.warning(
            "Could not determine flag for ip: {}".format(ipaddr))
        return url_for('static', filename=constants.DEFAULT_FLAG_URL)
    else:
        # Constructs the flag source using country code
        flag = flag_path.format(ccode.upper())
        local_flag_path = '/static/img/flags-iso/shiny/64/{}.png'.format(
            ccode.upper())

        if os.path.exists(MHN_SERVER_HOME + "/mhn"+local_flag_path):
            return flag
        else:
            return url_for('static', filename=constants.DEFAULT_FLAG_URL)

          
def _get_country_ip(ipaddr):
    geo_api = 'https://api.ipgeolocationapi.com/geolocate/{}'
    try:
        # Using threatstream's geospray API to get
        # the country name for this IP address.
        r = requests.get(geo_api.format(ipaddr))
        name = r.json()['un_locode']
        return name
    except Exception:
        app.logger.warning("Could not determine country name for ip: {}".format(ipaddr))
        return constants.DEFAULT_COUNTRY_NAME
