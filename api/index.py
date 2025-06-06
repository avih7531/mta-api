from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import math
from underground import SubwayFeed, metadata
from datetime import datetime

app = Flask(__name__)
CORS(app)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def get_station_routes():
    """Load the station routes from our JSON file"""
    try:
        with open('station_routes.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: station_routes.json not found")
        return {}

def get_departures(station_id, route):
    """
    Get the next 3 departures for a specific route at a station, separated by direction
    """
    try:
        # Get the feed for this route using the Python API
        feed = SubwayFeed.get(route)
        
        # Get the stop times dictionary
        stop_dict = feed.extract_stop_dict()
        
        # Initialize departures for both directions
        north_departures = []
        south_departures = []
        
        # Find the stop times for our station
        for route_id, stops in stop_dict.items():
            # Only process stops for our specific route
            if route in route_id:
                for stop_id, times in stops.items():
                    # Check for North bound
                    if stop_id == f"{station_id}N":
                        # Sort times and get next 3
                        sorted_times = sorted(times)
                        north_departures = [t.strftime('%H:%M') for t in sorted_times[:3]]
                    # Check for South bound
                    elif stop_id == f"{station_id}S":
                        # Sort times and get next 3
                        sorted_times = sorted(times)
                        south_departures = [t.strftime('%H:%M') for t in sorted_times[:3]]
        
        return {
            'north': north_departures,
            'south': south_departures
        }
    except Exception as e:
        print(f"Error getting departures for {route} at {station_id}: {e}")
        return {'north': [], 'south': []}

def find_nearest_station(user_lat, user_lon):
    """
    Find the nearest subway station to the given coordinates
    Returns the station ID and name
    """
    with open('stations.json', 'r') as f:
        stations = json.load(f)
    
    nearest_station = None
    min_distance = float('inf')
    
    for station_id, station_data in stations.items():
        station_lat, station_lon = map(float, station_data['stop_coordinates'].split(','))
        distance = haversine_distance(user_lat, user_lon, station_lat, station_lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest_station = {
                'id': station_id,
                'name': station_data['stop_name'],
                'distance': distance,
                'coordinates': station_data['stop_coordinates'],
                'n_id': station_data['n_ID'],
                's_id': station_data['s_ID']
            }
    
    return nearest_station

@app.route('/nearest-station', methods=['GET'])
def get_nearest_station():
    try:
        # Get latitude and longitude from query parameters
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({
                'error': 'Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180'
            }), 400
        
        # Find nearest station
        nearest = find_nearest_station(lat, lon)
        
        if nearest:
            # Get station routes
            station_routes = get_station_routes()
            
            # Find which routes serve this station
            serving_routes = []
            for route, stations in station_routes.items():
                if nearest['id'] in stations:
                    # Get departures for this route
                    departures = get_departures(nearest['id'], route)
                    if departures['north'] or departures['south']:  # Only add routes that have departures
                        serving_routes.append({
                            'route': route,
                            'departures': departures
                        })
            
            # Format the response for easy display in Shortcuts
            formatted_response = {
                'station_name': nearest['name'],
                'distance': f"{nearest['distance']:.2f} km",
                'trains': []
            }
            
            # Add each train's information
            for route_info in serving_routes:
                train_info = {
                    'line': route_info['route'],
                    'northbound': ' → '.join(route_info['departures']['north']) if route_info['departures']['north'] else 'No trains',
                    'southbound': ' → '.join(route_info['departures']['south']) if route_info['departures']['south'] else 'No trains'
                }
                formatted_response['trains'].append(train_info)
            
            # Create a human-readable summary
            summary = f"🚉 {nearest['name']}\n"
            summary += f"📍 {nearest['distance']:.2f} km away\n\n"
            
            if formatted_response['trains']:
                summary += "Next Departures:\n"
                for train in formatted_response['trains']:
                    summary += f"🚂 {train['line']} train:\n"
                    summary += f"   Northbound: {train['northbound']}\n"
                    summary += f"   Southbound: {train['southbound']}\n"
            else:
                summary += "No trains currently scheduled"
            
            return jsonify({
                'formatted': formatted_response,
                'summary': summary,
                'raw_data': nearest,  # Keep the raw data for advanced users
                'status': 'success'
            })
        else:
            return jsonify({
                'error': 'No stations found',
                'status': 'error'
            }), 404
            
    except ValueError:
        return jsonify({
            'error': 'Invalid parameters. Please provide valid latitude and longitude as numbers.',
            'status': 'error'
        }), 400
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
