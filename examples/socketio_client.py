import logging
import usocketio.client

logging.basicConfig(level=logging.DEBUG)

def main():
    # Add code here to join your Local Network
    socketio = usocketio.client.connect('http://YOURLOCALNETWORKIPHERE:SERVERPORT/')

    @socketio.on('message')
    def on_message(self, message):
        print("message", message)

    @socketio.on('alert')
    def on_alert(self, message):
        print("alert", message)

    while True:
        try:
            socketio.run()
        except KeyboardInterrupt:
            socketio.close()
            break

if __name__ == "__main__":
    main()
