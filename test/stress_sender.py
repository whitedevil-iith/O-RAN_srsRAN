import socket
import time

HOST = '127.0.0.1'  # Server address
PORT = 12345        # Port to connect

def send_message(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(message.encode())

if __name__ == "__main__":
    # Send 5 to trigger CPU overload
    print("Sending 5 to trigger CPU overload...")
    send_message("5")

    # Wait and then stop it
    time.sleep(5)
    print("Stopping CPU overload...")
    send_message("END")
