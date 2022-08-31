"""
Copyright (C) 2022 Julian Metzler

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import datetime
import requests

from dateutil import parser as dt_parser


class FraportAPI:
    def __init__(self):
        pass
    
    def _convert_flight_dict(self, flight, is_arrival):
        """
        Convert a flight data dict from the Fraport API format to our format.
        This mostly means renaming keys.
        
        is_arrival: Used to rename arrival/departure time keys
        """
        scheduled_arrival_key = 'sched' if is_arrival else 'schedArr'
        scheduled_departure_key = 'schedDep' if is_arrival else 'sched'
        estimated_arrival_key = 'esti' if is_arrival else 'estiArr'
        estimated_departure_key = 'estiDep' if is_arrival else 'esti'
        
        out = {
            'aircraft_icao': flight.get('ac'),
            'aircraft_registration': flight.get('reg'),
            'airline_iata': flight.get('al'),
            'airline_name': flight.get('alname'),
            'airport_iata': flight.get('iata'),
            'airport_name': flight.get('apname'),
            'baggage_claims': flight.get('bag'),
            'codeshares': flight.get('cs'),
            'counters': flight.get('schalter'),
            'duration': datetime.timedelta(minutes=flight.get('duration')) if flight.get('duration') else None,
            'estimated_arrival': dt_parser.parse(flight.get(estimated_arrival_key)) if flight.get(estimated_arrival_key) else None,
            'estimated_departure': dt_parser.parse(flight.get(estimated_departure_key)) if flight.get(estimated_departure_key) else None,
            'exit': flight.get('ausgang'),
            'flight_id': flight.get('id'),
            'flight_number': flight.get('fnr'),
            'flight_status': flight.get('flstatus'), # unclear
            'gate': flight.get('gate'),
            'hall': flight.get('halle'),
            'language': flight.get('lang'),
            'last_update': dt_parser.parse(flight.get('lu')) if flight.get('lu') else None,
            's': flight.get('s'), # unclear
            'scheduled_arrival': dt_parser.parse(flight.get(scheduled_arrival_key)) if flight.get(scheduled_arrival_key) else None,
            'scheduled_departure': dt_parser.parse(flight.get(scheduled_departure_key)) if flight.get(scheduled_departure_key) else None,
            'status': flight.get('status'),
            'stops': flight.get('stops'),
            'terminal': flight.get('terminal'),
            'type': flight.get('typ'), # unclear
            'via_iata': flight.get('rou'),
            'via_name': flight.get('rouname')
        }
        return out
    
    def get_flights(self, flight_type='departures', count=10, lang="en", page=1, timestamp=None):
        """
        Get flight data
        
        flight_type: departures or arrivals
        count: How many flights to retrieve
        lang: Language for status fields in response
        page: which page of the results to get
        """
        get_params = {
            'perpage': count,
            'lang': lang,
            'page': page,
            'flighttype': flight_type,
            'time': (timestamp or datetime.datetime.utcnow()).strftime('%Y-%m-%dT%H:%M:00.000Z')
        }
        is_arrival = flight_type == 'arrivals'
        resp = requests.get("https://www.frankfurt-airport.com/de/_jcr_content.flights.json/filter", params=get_params)
        data = resp.json()
        #with open("out.json", 'r') as f:
        #    data = json.load(f)
        #with open("out.json", 'w') as f:
        #    json.dump(data, f)
        data['flights'] = [self._convert_flight_dict(flight, is_arrival=is_arrival) for flight in data['data']]
        del data['data']
        return data
