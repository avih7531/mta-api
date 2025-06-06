from underground import SubwayFeed, metadata
import json


def update_stations():
    all_routes = [
        "1", "2", "3", "4", "5", "6",
        "A", "C", "E", "B", "D", "F", "M",
        "N", "Q", "R", "W", "L", "J", "Z",
        "G", "FS", "GS", "H", "SI",
    ]
    results = {}
    
    for route in all_routes:
        if not route:  # Safeguard to ensure route is not empty
            print(f"Warning: Skipping empty route")
            continue

        try:
            # Get the feed for this route using the Python API
            feed = SubwayFeed.get(route)
            
            # Get the stop times dictionary
            stop_dict = feed.extract_stop_dict()
            
            # Extract unique station IDs (without N/S suffix) that have current service
            route_results = set()
            for route_id, stops in stop_dict.items():
                # Only process stops for our specific route
                if route in route_id:
                    for stop_id, times in stops.items():
                        # Only include stations that have current service
                        if times:  # If there are any times, the station is being served
                            # Remove N/S suffix if present
                            if stop_id[-1] in ['N', 'S']:
                                stop_id = stop_id[:-1]
                            route_results.add(stop_id)
            
            # Convert set to sorted list
            route_results = sorted(list(route_results))
            
            if route_results:
                results[route] = route_results
                print(f"Found {len(route_results)} active stations for route {route}")
            else:
                print(f"Warning: No active stations found for route {route}")
                
        except Exception as e:
            print(f"Error processing route {route}: {e}")
            continue
    
    # Save results to a JSON file
    try:
        with open('station_routes.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("Successfully saved station routes to station_routes.json")
    except Exception as e:
        print(f"Error saving to file: {e}")

if __name__ == "__main__":
    update_stations()
