# Shared Code

The Shared code represents code that is used by both the Car and the Pit applications.

It consists of several components

## Protobuf Message Definitions

Lemon-Pi uses Google's protobuf message definition mechanism to create tightly packed on the wire messages.
The proto definition is in [shared/protos/messages.proto](shared/protos/messages.proto)
There is an additional explanation in the [protos directory](shared/protos/) 

## Lora Radio Control 

This is a thread that listens for radio messages, but it pings at random intervals to let other radios in the same group know that it is operating.
More details can be found in [shared/radio.py](shared/radio.py)

## An Event Framework
This is a simple framework that allows the definition of concrete event objects, and the emitting of that event along with the registration of interest in that event.


e.g.
```python
  MyEvent = Event("mine")

  # at any point in the code where this event needs to be emitted
  MyEvent.emit()

  # code that needs to be notified of the event occurring should, in its constructor, register its interest...
  MyEvent.register_handler(self)
```
The base definition can be found in [shared/events.py](shared/events.py)

Event definitions are all grouped together into a single file.

For the car, they are in [car/event_defs.py](car/event_defs.py)

For the pit, they are in [pit/event_defs.py](pit/event_defs.py)

This event framework is very straightforward and is not threaded. So the thread that emits the event synchronously traverses all the registered handlers.

## A USB detector
This can tell which piece of hardware (GPS / Lora / OBD) is plugged into each USB port.
