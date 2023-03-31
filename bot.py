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

    def __init__(self, loc):
        self.weather_url = "https://api.open-meteo.com/v1/forecast?"
        self.weather_query = (
            "latitude="
            + str(loc.latitude)
            + "&longitude="
            + str(loc.longitude)
            + "&hourly=cloudcover&timezone="
            + loc.continent
            + "/"
            + loc.city
        )
        self.data = ""

    def get_data(self):
        """ Returns raw weather data """
        return self.data

    def get_coverage(self):
        """ Returns cloud coverage conditions """
        with urllib.request.urlopen(self.weather_url + self.weather_query) as response:
            self.data = json.loads(response.read().decode("utf-8"))

        # lookup current hour in the response, example: "2023-03-31T15:00"
        hourly_key = datetime.now().strftime("%Y-%m-%dT%H:00")
        coverage_idx = self.data["hourly"]["time"].index(hourly_key)
        return self.data["hourly"]["cloudcover"][coverage_idx]


class Satellite:
    """ Retrieve orbital parameters of the selected LEO object """

    def __init__(self, name):
        if not os.path.isfile("stations.txt"):
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
        condx = W.get_coverage()
        if condx < 100:
            STATUS_LINE = (
                "#ISS flying over #Vilnius: azimuth "
                + str(int(AZIMUTH))
                + " degrees, cloud coverage: "
                + str(condx)
                + "%"
            )
            TWEET.statuses.update(status=STATUS_LINE)
            print("Tweeted: " + STATUS_LINE)
        else:
            print("Cloud coverage is " + str(condx) + " percent. Not tweeting")
    else:
        print("Elevation: " + str(SAT.elevation(LOC)))

    time.sleep(os.environ.get("BOT_SLEEP_TIME", 60))
