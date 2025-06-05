# Main Blueprint

This module defines the user-facing experience of the Molecular Oncology Almanac Browser. All views accessible to visitors of the website are managed within this blueprint.

## File Structure

- `__init__.py`  
  Initializes the blueprint and registers routes with the Flask application.

- `routes.py`  
  Defines Flask routes (endpoints) and handles request/response interactions.  
  Delegates data handling and transformation to `services.py`, `handlers.py`, and `requests.py`.

- `handlers.py`  
  Interfaces with the local cached database using SQLAlchemy.  
  Focuses on data retrieval, filtering, and persistence logic.

- `requests.py`  
  Provides interfaces for retrieving data from both the [Molecular Oncology Almanac API](https://github.com/vanallenlab/moalmanac-api) and the local SQLite database.  
  The `API` class handles outbound HTTP requests.  
  The `Local` class uses SQLAlchemy handlers to query and return cached data.

- `services.py`  
  Contains intermediate logic for processing or transforming data before it is passed to routes for rendering.  
  Aggregates, filters, and formats data returned from `handlers.py` and `requests.py`.

