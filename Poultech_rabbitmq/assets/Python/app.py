from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import pika
import json
import threading
import os
import cv2

app = Flask(__name__, template_folder='../../', static_folder='../../assets')
socketio = SocketIO(app)

rabbitmq_url = "amqps://uhbvmhoj:u76Em_OYzjlBXtV3Zw0K4MeGEI4XHEFu@hawk.rmq.cloudamqp.com/uhbvmhoj"
queue_name = "Testing0"
topic = "1001I/DATA"

# Dictionaries to store the latest data for each device
latest_data = {
    "index": {"temperature": None, "humidity": None, "co2": None, "ammonia": None, "other": None},
    "1001A": {"temperature": None, "humidity": None, "co2": None, "ammonia": None, "other": None},
    "1001C": {"temperature": None, "humidity": None, "co2": None, "ammonia": None, "other": None},
    "1001H": {"temperature": None, "humidity": None, "co2": None, "ammonia": None, "other": None},
    "1001I": {"temperature": None, "humidity": None, "co2": None, "ammonia": None, "other": None},
    "1001J": {"temperature": None, "humidity": None, "co2": None, "ammonia": None, "other": None},
}

# Consumer function to read sensor values from RabbitMQ
def consume_sensor_data():
    params = pika.URLParameters(rabbitmq_url)

    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declare and bind the queue
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_bind(exchange="amq.topic", queue=queue_name, routing_key=topic)

        # Callback function for processing messages
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body.decode())
                device_id = message.get('DEVICE_ID')  # Extract device ID from the message

                if device_id in latest_data:  # Update data for the corresponding device
                    device_data = latest_data[device_id]

                    # Update data only if keys exist and have values
                    if 'TEMP' in message and message['TEMP'] != "":
                        device_data["temperature"] = float(message['TEMP'])
                    if 'HUM' in message and message['HUM'] != "":
                        device_data["humidity"] = float(message['HUM'])
                    if 'R1' in message and message['R1'] != "":
                        device_data["co2"] = float(message['R1'])
                    if 'R2' in message and message['R2'] != "":
                        device_data["ammonia"] = round(float(message['R2']))
                    if 'R3' in message and message['R3'] != "":
                        device_data["other"] = round(float(message['R3']))

                    print(f"Updated data for {device_id}: {device_data}")

                    # Emit updated data to clients via Socket.IO for the specific device
                    socketio.emit(f'update_data_{device_id}', device_data)
            except Exception as e:
                print(f"Error processing message: {e}")

        # Start consuming messages
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        print(f"Subscribed to topic: {topic}")
        channel.start_consuming()
    except Exception as e:
        print(f"Error: {e}")

# Start the consumer in a separate thread
threading.Thread(target=consume_sensor_data, daemon=True).start()

# Function to generate video frames (unchanged)
def gen():
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"Video file not found at {VIDEO_PATH}")

    cap = cv2.VideoCapture(VIDEO_PATH)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cap.release()
        print("Video capture released.")

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/1001A.html')
def device_1001A():
    return render_template('1001A.html')

@app.route('/1001C.html')
def device_1001C():
    return render_template('1001C.html')

@app.route('/1001H.html')
def device_1001H():
    return render_template('1001H.html')

@app.route('/1001I.html')
def device_1001I():
    return render_template('1001I.html')

@app.route('/1001J.html')
def device_1001J():
    return render_template('1001J.html')

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
