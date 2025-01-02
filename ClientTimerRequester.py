import socket
import logging
from logging.handlers import RotatingFileHandler
import threading
import uuid
import argparse

# Set up the logger with RotatingFileHandler
log_file = "logs/ClientTimerRequester.log"
max_log_size = 2 * 1024 * 1024  # 2 MB

# Set up the rotating file handler
rotating_handler = RotatingFileHandler(log_file, maxBytes=max_log_size)

# Set the logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

# Set up the root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[rotating_handler, logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S',  # Customize the date format
)

Logger = logging.getLogger()

# Main Client class
class ClientTimerRequester:
    def __init__(self, num_msgs, host, port, timeout):
        self.num_msgs = num_msgs
        self.host = host
        self.port = port
        self.timeout = timeout  # Timeout in seconds for both send and recv
        self.running = threading.Event()
        self.initialized = False
        self.running.set()  # Set to True initially, Signal for running threads

    # Check if the 
    def isInitialized(self):
        return self.initialized

    # Create socket, stablish connection and then send messages
    def start(self):
        self.initialized = True
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port)) # Connect to the server socket
            self.client_socket.settimeout(self.timeout)  # Set timeout for socket operations
            Logger.info(f"Connected to server {self.host}:{self.port}")
        except Exception as e:
            Logger.error(f"Failed to connect to server: {e}")

        client_thread = threading.Thread(target=self.send_messages) # start thread to send messages
        client_thread.start()
        client_thread.join()  # Wait for the input loop to finish
    
    # Send messages to the Server and handles the response
    def send_messages(self):
        assert self.initialized, "Client not started yet!"
        num_msgs_sent = 0
        while self.running.is_set():
            try:
                if num_msgs_sent < self.num_msgs:
                    # Generate a random UUID
                    random_uuid = uuid.uuid4()
                    message = str(random_uuid).lower()
                    Logger.info(f"Sending UUID: {random_uuid}")
                    self.client_socket.send(message.encode())
                    response = self.client_socket.recv(1024).decode()
                    logging.info(f"Server response: {response}")
                    num_msgs_sent += 1
                else:
                    self.running.clear()  # Stop the loop
                    Logger.info(f"Total number of sent messages have been reached.")
                    break
            except Exception as e:
                logging.error(f"Error sending or receiving messages: {e}")
                self.shutdown()  # Stop on error

        self.shutdown() # All done, disconnect from Server and quit program

    # Free resources before quit
    def shutdown(self):
        Logger.info("Client shutdown started...")
        self.initialized = False
        self.running.clear()
        try:
            self.client_socket.close()
            Logger.info("Disconnected from server.")
        except Exception as e:
            Logger.error(f"Error closing socket: {e}")
        Logger.info("Client shutdown ended! Bye bye...")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="TCP ClientTimerRequester: Sends a string to the Server and gets the delta time from latest message.")
    parser.add_argument(
        "--num_msgs", type=int, required=True, help="Total Number of messages to be sent to the Server (e.g.: 20)"
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Server address to connect to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=47945, help="Port number to connect to (default: 47945)"
    )
    parser.add_argument(
        "--timeout", type=int, default=5, help="Timeout for socket operations (default: 5 seconds)"
    )
    args = parser.parse_args()

    client = ClientTimerRequester(num_msgs=args.num_msgs, host=args.host, port=args.port, timeout=args.timeout)
    try:
        client.start()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received.")
        client.shutdown()
