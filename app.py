from flask import Flask, request, jsonify
import redis
import time
import json

app = Flask(__name__)

# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Constants for rate limiting
MAX_REQUESTS = 5  # Maximum number of requests allowed
TIME_WINDOW = 60   # Time window in seconds

def rate_limit():
    user_ip = request.remote_addr  # Get user IP
    now = int(time.time())  # Current timestamp

    # Get the current request record for the user
    record = redis_client.get(user_ip)

    # If there is no record, initialize it
    if record is None:
        requests = {'count': 1, 'first_request': now}
    else:
        requests = json.loads(record)

    # Check if rate limit exceeded
    if requests['count'] >= MAX_REQUESTS and (now - requests['first_request']) < TIME_WINDOW:
        return jsonify({'error': 'Too Many Requests. Please try again later.'}), 429

    # Update request count
    if now - requests['first_request'] > TIME_WINDOW:
        # Reset the count if the time window has passed
        requests = {'count': 1, 'first_request': now}
    else:
        requests['count'] += 1  # Increment the count

    # Store the updated requests record back to Redis with expiration time
    redis_client.set(user_ip, json.dumps(requests), ex=TIME_WINDOW)

    return None  # No error, continue to the next handler

@app.route('/')
def home():
    rate_limit_response = rate_limit()  # Call rate limit function
    if rate_limit_response:  # Check if there's an error response
        return rate_limit_response

    return "Welcome to the API!"

if __name__ == "__main__":
    app.run(port=3000)
