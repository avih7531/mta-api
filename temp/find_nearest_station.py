import json
import math

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
                'distance': distance
            }
    
    return nearest_station

if __name__ == "__main__":
    # Example usage
    test_lat = 40.7128  # Example latitude (NYC)
    test_lon = -74.0060  # Example longitude (NYC)
    
    nearest = find_nearest_station(test_lat, test_lon)
    print(f"Nearest station: {nearest['name']} (ID: {nearest['id']})")
    print(f"Distance: {nearest['distance']:.2f} km") 