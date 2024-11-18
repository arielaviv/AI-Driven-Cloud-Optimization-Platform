from flask import Flask, jsonify, request
import redis
import boto3
import json

app = Flask(__name__)

# Initialize Redis client
redis_client = redis.Redis(host="redis", port=6379)

# Initialize AWS Cost Explorer client
client = boto3.client('ce', region_name='us-east-1')

# Route to test Redis
@app.route('/redis-test', methods=['GET'])
def test_redis():
    redis_client.set("test", "Redis is running!")
    return redis_client.get("test").decode("utf-8")

# Route to fetch billing data from AWS Cost Explorer
@app.route('/billing', methods=['GET'])
def get_billing():
    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': '2023-11-01',
                'End': '2023-11-30'
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to fetch cached billing data or cache fresh data
@app.route('/cached-billing', methods=['GET'])
def get_cached_billing():
    try:
        cached_data = redis_client.get('billing')
        if cached_data:
            return jsonify(json.loads(cached_data))
        else:
            # Fetch fresh data from AWS Cost Explorer
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': '2023-11-01',
                    'End': '2023-11-30'
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            # Cache the data for 1 hour (3600 seconds)
            redis_client.set('billing', json.dumps(response), ex=3600)
            return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to terminate resources, for example, terminating an EC2 instance
@app.route('/terminate', methods=['POST'])
def terminate_resource():
    data = request.json
    resource_id = data.get('resource_id', None)
    
    if not resource_id:
        return jsonify({"error": "resource_id is required"}), 400
    
    try:
        # Connect to EC2
        ec2 = boto3.client('ec2', region_name='us-east-1')
        
        # Terminate the instance
        response = ec2.terminate_instances(InstanceIds=[resource_id])
        return jsonify({"message": f"Resource {resource_id} terminated successfully!", "response": response})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to fetch mock resource usage data
@app.route('/usage', methods=['GET'])
def get_usage():
    return jsonify({
        "resources": [
            {"name": "EC2", "usage": 75},
            {"name": "S3", "usage": 40},
            {"name": "Lambda", "usage": 90}
        ]
    })

# Health check route
@app.route('/', methods=['GET'])
def home():
    return "Backend is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
