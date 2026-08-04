# Day 21 — REST API Basics

## What I Tested
Used `curl` to make GET requests to two public APIs and observed the raw responses.

## Test 1: JSONPlaceholder (fake test data)
Command:
curl https://jsonplaceholder.typicode.com/posts/1

Response: JSON object with userId, id, title, body fields. Status 200 OK.

## Test 2: Open-Meteo (real weather data)
Command:
curl "https://api.open-meteo.com/v1/forecast?latitude=31.5&longitude=74.3&current_weather=true"

Response: Real-time weather for Lahore — temperature 33.6°C, windspeed 4.5 km/h.

## Test 3: Headers with -i flag
Command:
curl -i https://jsonplaceholder.typicode.com/posts/1

Key headers observed:
- HTTP/1.1 200 OK — status line, confirms request succeeded
- Content-Type: application/json — tells client how to parse the body
- x-ratelimit-limit / x-ratelimit-remaining / x-ratelimit-reset — same rate limit concept we hit earlier with OpenRouter's 429 error, but here it's shown proactively before you run out

## Test 4: Invalid request (404)
Command:
curl -i https://jsonplaceholder.typicode.com/posts/99999

Result: Status 404 Not Found, body was just {} (empty object, no error message).

## Key Takeaway
Status code is the real signal of success/failure, not just the response body — 
a body can be empty in both success and failure cases. Every request (even a 404) 
still counts against the rate limit.