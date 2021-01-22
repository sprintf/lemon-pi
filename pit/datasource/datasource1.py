
import time
import urllib.request
import json
import websocket
from threading import Thread

from pit.datasource.datasource_handler import DataSourceHandler

source = 'rotinom-ecar'[::-1]


class DataSource(Thread):

    def __init__(self, race_id, handler:DataSourceHandler):
        Thread.__init__(self)
        self.race_id = race_id
        self.handler = handler
        self.stopping = False
        self.stream_url = None
        self.ws = None

    def connect(self) -> bool:
        now = int(time.time())
        with urllib.request.urlopen(
                'https://api.{}.com/Info/WebRaceList?accountID=&seriesID=&raceID={}&styleID=&t={}'.
                        format(source, self.race_id, now)) as response:
            json_response = response.read()
            stream_data = json.loads(json_response)
            race = stream_data['CurrentRaces'][0]
            live_timing_token = stream_data['LiveTimingToken']
            live_timing_host = stream_data['LiveTimingHost']

            self.stream_url = 'wss://{}/instance/{}/{}'.format(live_timing_host, race['Instance'], live_timing_token)
        return self.stream_url is not None

    def run(self):
        if self.stream_url is None:
            raise Exception("successful connect() needed first")

        def on_message(ws, message):
            self.handler.handle_message(message)

        def on_error(ws, error):
            print("error: {}".format(error))

        def on_close(ws):
            print("WS closed")

        def on_open(ws):
            print("Opened!")

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(self.stream_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        self.ws.on_open = on_open
        self.ws.run_forever()

    def stop(self):
        self.stopping = True
        if self.ws:
            self.ws.close()


