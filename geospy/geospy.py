#! /usr/bin/env python
import abc
import argparse
import errno
import gps
import math
import logging
import netifaces
import os
import Queue
import socket
import sys
import threading
import time

import requests

import db_api
import wifi_scanner

GPS_POLL_INTERVAL = 10
WPS_POLL_INTERVAL = 30

NaN = float('nan')

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_TEMPLATE = os.path.join(CUR_DIR, 'map_template.html')
MAPS_OUTPUT_FILE = os.path.join(CUR_DIR, 'out.html')

GOOGLE_API_KEY = None


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
class GeoPosition(object):
    def __init__(self, latitude=NaN, longitude=NaN,
                 epx=NaN, epy=NaN, accuracy=NaN, service_name=None):
        self.service_name = service_name
        # self.timestamp = timestamp or time.time()

        self.latitude = latitude
        self.longitude = longitude
        #  Longitude Err [+/- m]
        self.epx = epx
        # Latitude Err:  [+/- m]
        self.epy = epy

        # accuracy is the radius [m] around the location
        if math.isnan(accuracy):
            self.accuracy = max(epx, epy) / 2
        else:
            self.accuracy = accuracy

    def __str__(self):
        return 'service:   {}\n' \
               'latitude:  {}\n' \
               'longitude: {}\n' \
               'epx:       {}\n' \
               'epy:       {}\n' \
               'accuracy:  {}\n'.format(self.service_name,
                                        self.latitude,
                                        self.longitude,
                                        self.epx,
                                        self.epy,
                                        self.accuracy)


class PositionService(threading.Thread):
    __metaclass__ = abc.ABCMeta

    def __init__(self, position_q, poll_interval):
        super(PositionService, self).__init__()
        self.position_q = position_q
        self._poll_interval = poll_interval
        self.running = True

    @abc.abstractmethod
    def poll(self):
        pass


class GpsService(PositionService):
    def __init__(self, position_q, poll_interval=GPS_POLL_INTERVAL,
                 verbose=0):
        super(GpsService, self).__init__(position_q, poll_interval)
        self._gpsd = None

    def _set_position(self):
        if self._gpsd.fix.mode not in (gps.MODE_2D, gps.MODE_3D):
            return
        gps_fix = self._gpsd.fix
        self.position_q.put(GeoPosition(gps_fix.latitude, gps_fix.longitude,
                                        gps_fix.epx, gps_fix.epy,
                                        service_name=self.__class__.__name__))

    def _wait_for_gpsd(self):
        """ Busy wait for gpsd socket.

        GPSD is loaded by udev after first gps device is plugged. This function
        waits until the system presents a device. In case the device gets
        removed, the gpsd remains, so we don't handle that case for now.
        """
        while self.running and not self._gpsd:
            logging.debug('waiting for gpsd socket')
            try:
                self._gpsd = gps.gps(
                    mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
                logging.info('connected to gpsd')
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    logging.error(
                        'gpsd refused connection, gps device is missing')
                    time.sleep(10)

    def poll(self):
        logging.debug('waiting for data from gpsd')
        if self._gpsd.waiting(self._poll_interval):
            self._gpsd.next()
            self._set_position()

    def run(self):
        self._wait_for_gpsd()
        while self.running:
            self.poll()

    @property
    def fix(self):
        return self._gpsd.fix

    @property
    def satellites(self):
        return self._gpsd.satellites

    def join(self, timeout=None):
        # the gps client's socket potentially blocks on recv, and can prevent
        # the process's normal exit flow (unless SIGKILLED)
        self.running = False
        if self._gpsd and self._gpsd.sock:
            self._gpsd.sock.shutdown(socket.SHUT_RDWR)
            self._gpsd.close()
        super(GpsService, self).join(timeout)


class WifiPositionService(PositionService):
    __metaclass__ = abc.ABCMeta

    def __init__(self, position_q, api_key, poll_interval=WPS_POLL_INTERVAL):
        super(WifiPositionService, self).__init__(position_q, poll_interval)
        self._beacons = []
        self._api_key = api_key
        self._interfaces = [n for n in netifaces.interfaces() if
                            n.startswith('wlan')]
        self._api_url = self.base_url + self._api_key

    @property
    def api_key(self):
        return self._api_key

    @abc.abstractproperty
    def base_url(self):
        pass


class GooglePositionService(WifiPositionService):
    base_url = 'https://www.googleapis.com/geolocation/v1/geolocate?key='

    @classmethod
    def _beacon_to_google_api(cls, beacon):
        return {
            "macAddress": beacon['Address'],
            "signalStrength": beacon['Signal'],
            "channel": beacon['Channel'],
        }

    def _create_request_data(self):
        """ Creates a request body to query Gooogle's API.

         The request asssembled as described at:
         https://developers.google.com/maps/documentation/geolocation/

        :return: str -> json formatted request string
        """
        return {
            'considerIp': 'true',
            'wifiAccessPoints': [self._beacon_to_google_api(beacon) for
                                 beacon in self._beacons]
        }

    def _set_position(self, pos_dict):
        location = pos_dict['location']
        self.position_q.put(
            GeoPosition(location['lat'], location['lng'],
                        accuracy=pos_dict['accuracy'],
                        service_name=self.__class__.__name__))

    def _post_position_request(self):
        data = self._create_request_data()
        logging.debug('posting data to: {}'.format(self._api_url))
        try:
            response = requests.post(self._api_url, json=data)
            return response.json()
        except requests.RequestException as e:
            logging.error('error fetching data: {}'.format(e))

    def _scan_beacons(self):
        logging.debug('scanning nearby wifi beacons')
        try:
            self._beacons = wifi_scanner.scan(self._interfaces)
        except OSError as e:
            logging.error('Error while scanning {}'.format(e))
            self._beacons = None

    def _is_valid_response(self, resp):
        if not resp:
            return False
        if resp.get('error'):
            return False

        return True

    def poll(self):
        self._scan_beacons()
        if self._beacons:
            position_dict = self._post_position_request()
            if self._is_valid_response(position_dict):
                self._set_position(position_dict)
            else:
                logging.error('err response: {}'.format(position_dict))
        # TODO: switch to threading.Condition and wake on exit
        time.sleep(self._poll_interval)

    def run(self):
        while self.running:
            self.poll()

    def join(self, timeout=None):
        self.running = False
        super(GooglePositionService, self).join(timeout)


class PositionServicesScheduler(object):
    def __init__(self):
        super(PositionServicesScheduler, self).__init__()
        self.session = db_api.Session()
        self.position_q = Queue.Queue()

        self.position_services = [
            GpsService(self.position_q),
            GooglePositionService(
                self.position_q,
                api_key=GOOGLE_API_KEY)
        ]
        self.running = True

    def go(self):
        for service in self.position_services:
            service.start()
        while self.running:
            try:
                pos = self.position_q.get(timeout=2)
                logging.info('got position: {}'.format(pos))
                db_api.create_position_entry(
                    service_name=pos.service_name,
                    latitude=pos.latitude,
                    longitude=pos.longitude,
                    accuracy=pos.accuracy,
                    session=self.session)
            except Queue.Empty:
                pass

    def shutdown(self, timeout=None):
        for service in self.position_services:
            service.join(timeout)


# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
def validate_root_permissions():
    if os.geteuid() != 0:
        exit("You need to have root privileges to run this script.")


def validate_api_key(args):
    global GOOGLE_API_KEY
    try:
        GOOGLE_API_KEY = args.api_key or os.environ['GOOGLE_API_KEY']
    except KeyError:
        exit('API key was not provided. Set by --api-key or by '
             'export GOOGLE_API_KEY=')


def get_args():
    arg_parser = argparse.ArgumentParser(description='Location services')
    arg_parser.add_argument('-V', '--verbose', action='store_true',
                            default=False)
    arg_parser.add_argument('-Z', '--purge-db', action='store_true',
                            help='purge all local data', default=False)

    arg_parser.add_argument('-O', '--output-db', choices=['csv', 'maps'],
                            help='output db format')
    arg_parser.add_argument('-K', '--api-key', help='set api key')
    return arg_parser.parse_args()


def db_to_maps(session):
    map_template = open(MAPS_TEMPLATE, 'r').read()
    js_lines = []
    for p in session.query(db_api.Position).all():
        js_lines.append(
            '[\'{}\', \'{}\', \'{}\'],'.format(p.service.name,
                                               p.latitude,
                                               p.longitude,
                                               p.accuracy))
    replace_str = '\n'.join(js_lines)
    with open(MAPS_OUTPUT_FILE, 'w') as out_f:
        out_str = map_template.replace('@LOCATIONS@', replace_str)
        out_f.write(out_str)


def set_logging(level):
    logging.basicConfig(level=level)


def parse_args(args):
    if args.verbose:
        set_logging(level=logging.DEBUG)
    else:
        set_logging(level=logging.INFO)

    if args.purge_db:
        confirm = raw_input('dropping all data! [N/y]: ')
        if confirm.lower() in ('y', 'yes'):
            print('Dropped db')
            db_api.purge_db()
        sys.exit(0)

    if args.output_db:
        session = db_api.Session()
        if args.output_db == 'csv':
            db_api.db_to_csv(session)
            sys.exit(0)
        if args.output_db == 'maps':
            db_to_maps(session)
            sys.exit(0)
    validate_api_key(args)


def main():
    validate_root_permissions()

    args = get_args()
    parse_args(args)

    logging.info('geoposition starting')
    posistion_scheduler = PositionServicesScheduler()
    try:
        posistion_scheduler.go()
    except (KeyboardInterrupt, SystemExit):
        print('exiting')
        posistion_scheduler.running = False
        posistion_scheduler.shutdown()


if __name__ == '__main__':
    main()
