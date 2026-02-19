# WeatherFit

WeatherFit is a small client-side web app that fetches current weather data and recommends what to wear.

## Files

- `index.html` – app structure and accessible form controls
- `styles.css` – styling and keyboard focus states
- `app.js` – Open-Meteo API integration, weather rendering, localStorage persistence

## Setup / Run

No build tools are required.

1. Open a terminal in the repository root.
2. Start a static server (example):

   ```bash
   python3 -m http.server 8000
   ```

3. Open <http://localhost:8000/weatherfit/> in your browser.

## Manual test checklist

- [ ] The page title reads **WeatherFit**.
- [ ] I can type a city and click **Search**.
- [ ] Pressing **Enter** in the city input triggers the search.
- [ ] A loading message appears while API requests are in progress.
- [ ] If I enter an invalid city, an error appears (e.g., "City not found").
- [ ] For a valid city, city name, temperature (°C), wind speed, and weather description are displayed.
- [ ] The **Outfit suggestion** updates based on temperature and wind.
- [ ] The last searched city is saved and auto-loaded when I refresh/reopen the page.
- [ ] Keyboard focus styles are visible on the input and button.
