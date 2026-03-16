# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def get_weather(location: str) -> dict:
    """Gets the current weather for a location.
    
    Args:
        location: The city and state, e.g., 'San Francisco, CA'.
    """
    return {
        "location": location,
        "temperature": 68,
        "condition": "Sunny",
        "humidity": "45%",
        "wind": "10 mph NW",
        "forecast": [
            {"day": "Mon", "temperature": 68, "condition": "Sunny"},
            {"day": "Tue", "temperature": 70, "condition": "Sunny"},
            {"day": "Wed", "temperature": 65, "condition": "Partly Cloudy"}
        ]
    }

def find_restaurants(query: str, location: str) -> list[dict]:
    """Finds restaurants matching a query and location.
    
    Args:
        query: The type of food or restaurant name, e.g., 'Chinese', 'Pizza'.
        location: The location to search near, e.g., 'Current Location' or a city.
    """
    return [
        {
            "id": "1",
            "name": "Golden Dragon",
            "cuisine": "Chinese",
            "rating": 4.5,
            "reviews": 328,
            "price": "$$",
            "address": "123 Main St"
        },
        {
            "id": "2",
            "name": "Panda Express",
            "cuisine": "Chinese Fast Food",
            "rating": 3.8,
            "reviews": 145,
            "price": "$",
            "address": "456 Market St"
        },
        {
            "id": "3",
            "name": "Szechuan Palace",
            "cuisine": "Szechuan",
            "rating": 4.8,
            "reviews": 512,
            "price": "$$$",
            "address": "789 Broadway"
        }
    ]
