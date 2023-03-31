#!/usr/bin/python
""" Get twitter notifications on perfect observation conditions
    when the International Space Station flies over your city.
"""
# This Python file uses the following encoding: utf-8

import urllib
import json
import time
import re
import os

from datetime import datetime
from twitter import Twitter, OAuth
from pyorbital.orbital import Orbital


class Location:
    latitude = 54.687157
    longitude = 25.279652
    city = "Vilnius"
    continent = "Europe"


class Weather:
    """ Returns current weather conditions from wunderground """

    def __init__(self, location):
        self.weather_api_key = "d4388c6138a909c3"
        self.weather_url = "http://api.wunderground.com/api/"
        self.weather_query = "/conditions/q/" + location + ".json"
        self.data = ""

    def get_data(self):
        """ Returns raw weather data """
        return self.data

    def get_conditions(self):
        """ Returns observation conditions
            Possible values:
            http://wiki.wunderground.com/index.php/Educational_-_Partly_cloudy
        """
        with urllib.request.urlopen(
            self.weather_url + self.weather_api_key + self.weather_query
        ) as response:
            self.data = json.loads(response.read().decode("utf-8"))
        return self.data["current_observation"]["weather"]


class Satellite:
    """ Retrieve orbital parameters of the selected LEO object """

    def __init__(self, name):
        urllib.request.urlretrieve(
            "http://celestrak.com/NORAD/elements/stations.txt", "stations.txt"
        )
        self.orb = Orbital(name, "stations.txt")
        self.data = []

    def azimuth(self, loc):
        """ Return object azimuth """
        self.__update_data(loc)
        return self.data[0]

    def elevation(self, loc):
        """ Return object elevation """
        self.__update_data(loc)
        return self.data[1]

    def __update_data(self, loc):
        self.data = self.orb.get_observer_look(
            datetime.utcnow(), loc.longitude, loc.latitude, 1
        )

    def is_up(self, loc):
        """ Return object elevation """
        self.__update_data(loc)
        return True if self.data[1] > 5 else False


TWEET = Twitter(
    auth=OAuth(
        os.environ["TWITTER_TOKEN"],
        os.environ["TWITTER_TOKEN_SECRET"],
        os.environ["TWITTER_CONSUMER_KEY"],
        os.environ["TWITTER_CONSUMER_SECRET"],
    )
)

LOC = Location()
SAT = Satellite("ISS (ZARYA)")
W = Weather(LOC)

print("Main loop started")
while True:
    if SAT.is_up(LOC):
        AZIMUTH = SAT.azimuth(LOC)
        # calls on object w are expensive:
        CONDX = WU.get_conditions()
        if re.search("sunny|clear", CONDX, flags=re.I):
            STATUS_LINE = (
                "#ISS over #Vilnius: azimuth "
                + str(int(AZIMUTH))
                + " degrees, weather: "
                + CONDX.lower()
            )
            TWEET.statuses.update(status=STATUS_LINE)
            print("Tweeted: " + STATUS_LINE)
        else:
            print(CONDX)
    else:
        print("Elevation: " + str(SAT.elevation(LOC)))

    time.sleep(os.environ.get("BOT_SLEEP_TIME", 60))
