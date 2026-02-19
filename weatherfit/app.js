const form = document.getElementById('search-form');
const cityInput = document.getElementById('city-input');
const statusEl = document.getElementById('status');
const errorEl = document.getElementById('error');
const resultsEl = document.getElementById('results');
const resultCity = document.getElementById('result-city');
const resultTemp = document.getElementById('result-temp');
const resultWind = document.getElementById('result-wind');
const resultDesc = document.getElementById('result-desc');
const outfitText = document.getElementById('outfit-text');

const LAST_CITY_KEY = 'weatherfit.lastCity';

const weatherCodeDescriptions = {
  0: 'Clear sky',
  1: 'Mainly clear',
  2: 'Partly cloudy',
  3: 'Overcast',
  45: 'Fog',
  48: 'Depositing rime fog',
  51: 'Light drizzle',
  53: 'Moderate drizzle',
  55: 'Dense drizzle',
  56: 'Light freezing drizzle',
  57: 'Dense freezing drizzle',
  61: 'Slight rain',
  63: 'Moderate rain',
  65: 'Heavy rain',
  66: 'Light freezing rain',
  67: 'Heavy freezing rain',
  71: 'Slight snowfall',
  73: 'Moderate snowfall',
  75: 'Heavy snowfall',
  77: 'Snow grains',
  80: 'Slight rain showers',
  81: 'Moderate rain showers',
  82: 'Violent rain showers',
  85: 'Slight snow showers',
  86: 'Heavy snow showers',
  95: 'Thunderstorm',
  96: 'Thunderstorm with slight hail',
  99: 'Thunderstorm with heavy hail'
};

function setLoading(isLoading) {
  statusEl.textContent = isLoading ? 'Loading weather data…' : '';
  form.querySelector('button').disabled = isLoading;
}

function setError(message) {
  errorEl.textContent = message || '';
}

function getOutfitSuggestion(tempC, windKmh) {
  const parts = [];

  if (tempC <= 5) {
    parts.push('Wear a heavy coat, warm layers, and gloves.');
  } else if (tempC <= 12) {
    parts.push('Go with a jacket or sweater and long pants.');
  } else if (tempC <= 22) {
    parts.push('A light layer like a hoodie or long-sleeve shirt is a good fit.');
  } else {
    parts.push('Choose light, breathable clothes like a t-shirt and shorts.');
  }

  if (windKmh >= 30) {
    parts.push('It is windy, so add a windproof layer.');
  } else if (windKmh >= 18) {
    parts.push('A light windbreaker may help.');
  }

  return parts.join(' ');
}

async function geocodeCity(city) {
  const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&language=en&format=json`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Unable to fetch location data right now.');
  }

  const data = await response.json();
  if (!data.results || data.results.length === 0) {
    throw new Error('City not found. Try another search.');
  }

  return data.results[0];
}

async function fetchWeather(lat, lon) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,wind_speed_10m,weather_code`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Unable to fetch weather right now.');
  }

  const data = await response.json();
  if (!data.current) {
    throw new Error('No current weather data available.');
  }

  return data.current;
}

function renderWeather(location, weather) {
  const place = [location.name, location.country].filter(Boolean).join(', ');
  const temp = weather.temperature_2m;
  const wind = weather.wind_speed_10m;

  resultCity.textContent = place;
  resultTemp.textContent = `${temp.toFixed(1)} °C`;
  resultWind.textContent = `${wind.toFixed(1)} km/h`;
  resultDesc.textContent = weatherCodeDescriptions[weather.weather_code] || 'Unknown conditions';
  outfitText.textContent = getOutfitSuggestion(temp, wind);
  resultsEl.hidden = false;
}

async function searchCity(city) {
  setError('');
  setLoading(true);

  try {
    const location = await geocodeCity(city);
    const weather = await fetchWeather(location.latitude, location.longitude);

    renderWeather(location, weather);
    localStorage.setItem(LAST_CITY_KEY, city);
  } catch (error) {
    resultsEl.hidden = true;
    setError(error.message || 'Something went wrong.');
  } finally {
    setLoading(false);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const city = cityInput.value.trim();

  if (!city) {
    setError('Please enter a city name.');
    resultsEl.hidden = true;
    cityInput.focus();
    return;
  }

  await searchCity(city);
});

window.addEventListener('DOMContentLoaded', () => {
  const lastCity = localStorage.getItem(LAST_CITY_KEY);
  if (lastCity) {
    cityInput.value = lastCity;
    searchCity(lastCity);
  }
});
