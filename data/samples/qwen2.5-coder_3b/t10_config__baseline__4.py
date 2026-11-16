### Explanation

- **Settings Loading**: The `load_settings` function reads the `settings.toml` file using the `toml` library and returns a dictionary of settings.
- **FastAPI App Initialization**: The FastAPI app is initialized and configured with CORS settings from the loaded settings.
- **Health Endpoint**: The `/health` endpoint returns a JSON object indicating the health status of the app.
- **Root Endpoint**: A simple example route that returns a welcome message.

### Running the App

To run the FastAPI app, save the code in a file (e.g., `app.py`) and execute it:

