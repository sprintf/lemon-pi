import base64

import grpc
from google.protobuf.empty_pb2 import Empty

from lemon_pi_pb2 import SetFuelLevel, ToCarMessage
from lemon_pi_pb2_grpc import CommsServiceStub


def do_it():
    channel = grpc.insecure_channel('localhost:8080')
    stub = CommsServiceStub(channel)
    print("calling stub")
    r = stub.PingPong(Empty())
    print(r)
    print("done")

def do_it_secure():
    channel = grpc.insecure_channel("localhost:8080")
    stub = CommsServiceStub(channel)
    tc = ToCarMessage()
    tc.set_fuel.percent_full = 69
    tc.set_fuel.car_number = "999"
    r = stub.sendMessageFromCar(request=tc, metadata=build_auth_header("snma", "pit-999", "key"))
    print(r)
    print("done")

def build_auth_header(track_id:str, car_num: str, key:str):
    return [("authorization", f"Basic {create_auth_token(track_id, car_num, key)}")]

def create_auth_token(track_id:str, car_num: str, key:str):
    return base64.standard_b64encode(f"{track_id}/{car_num}:{key}".encode("utf-8")).decode('utf-8')


if __name__ == "__main__":
    do_it()
    do_it_secure()