
### Protobuf definitions

We use protobuf because message transmit/receive times are directly tied to the size of the data being sent.
A large message of 256 bytes (the largest supported by Lora) can take 6 seconds for the send/receive cycle.

Protobuf is fiddly, but it produces the tightest packed messages 