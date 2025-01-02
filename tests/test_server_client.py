import pytest
import threading
import time
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ClientTimerRequester import ClientTimerRequester
from ServerTimer import ServerTimer


@pytest.fixture
def start_server():
    """Fixture to start and stop the server."""

    server = ServerTimer(port=47946)
    server_thread = threading.Thread(target=server.start, daemon=True)  # Run server in a separate thread
    server_thread.start()  # Start the server

    time.sleep(1)  # Allow the server some time to start

    yield server  # Provide the server instance to the test
    server.shutdown()  # Ensure the server is stopped after the test
    server_thread.join() # Wait for shutdown to be finished (secket accept requires to have timeout)

def test_send_messages(start_server):
    """Test if the client and server can exchange messages."""
    client = ClientTimerRequester(1, "127.0.0.1", 47946, 3)
 
    isClientJobDone = False
    try:
        client.start()
        isClientJobDone = True
    except Exception as e:
        print(f"Error: {e}")

    assert isClientJobDone, "It is true is no exceptions and errors occurred."
    assert client.isInitialized() == False, "It is True if there is a connection to the Server."

def test_server_shutdown(start_server):
    """Test if the server can handle shutdown gracefully."""

    client = ClientTimerRequester(1, "127.0.0.1", 47946, 3)

    start_server.shutdown()
    time.sleep(1) # give time for the server clear resources

    isClientJobDone = False
    try:
        client.start()
        isClientJobDone = True
    except Exception as e:
        print(f"Error: {e}")

    assert isClientJobDone, "It is true is no exceptions and errors occurred."
    assert client.isInitialized() == False, "It is True if there is a connection to the Server."
    client.shutdown()
