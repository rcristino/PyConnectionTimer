import socket
import threading
import logging
from logging.handlers import RotatingFileHandler
import time
import argparse

# Set up the logger with RotatingFileHandler
log_file = "logs/ServerTimer.log"
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

# Main Server class
class ServerTimer:
    def __init__(self, port, host='0.0.0.0'):
        self.host = host
        self.port = port
        self.initialized = False
        
        self.threads = []  # Store client threads
        self.running = threading.Event()
        self.running.set()  # Set to True initially, Signal for running threads

    # Check if Server connection has been opened
    def isInitialized(self):
        return self.initialized
    
    # Client connection handler (one Client per thread)
    def handle_client(self, client_socket, client_address):
        assert self.initialized, "Client not started yet!"
        logging.info(f"Client connected: {client_address}")
        start_time = time.perf_counter()
        while self.running.is_set():
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                logging.info(f"Received from {client_address}: {message}")
                end_time = time.perf_counter()
                delta_time = end_time - start_time
                client_socket.send(f"UUID: {message} received after {delta_time:.6f} seconds".encode())  # send message to client
                start_time = time.perf_counter()

            except Exception as e:
                Logger.error(f"Error with client {client_address}: {e}")
                break
        client_socket.close()
        Logger.info(f"Client disconnected: {client_address}")

    # Free resources before quit
    def shutdown(self):
        Logger.info("Server shutdown started...")
        self.initialized = False
        self.running.clear()  # Signal threads to stop
        for thread in self.threads:
            thread.join()  # Wait for all threads to finish
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError as e:
                Logger.debug(f"Closing server socket: {e}")
            finally:
                self.server_socket = None
        Logger.info("Server shutdown ended! Bye bye...")

    # Initialize socket to listen client connections
    def start(self):
        self.initialized = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(5)  # Set timeout for accept() in seconds
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)  # Listen for up to 5 connections

        Logger.info(f"Server started on {self.host}:{self.port}")
        Logger.info("Server is running and waiting for connections...")

        while self.running.is_set() and self.server_socket:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.start()
                self.threads.append(client_thread)
            except socket.timeout:
                Logger.debug("No connection received. Retrying...")
            except OSError as e:
                Logger.debug(f"Problem with socket: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="TCP ServerTimer: Waits for Client connections and for each message received, it will send delta time from last message.")
    parser.add_argument(
        "--port", type=int, default=47945, help="Port number to listen for Clients (default: 47945)"
    )
    args = parser.parse_args()

    server = ServerTimer(port=args.port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.shutdown()
