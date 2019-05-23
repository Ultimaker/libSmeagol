# libSmeagol
Lib Smeagol is intended to store precious data for yourself, such as settings.
It stores key value pairs or sub groups (called subPocket(s)) of key/value pairs.
The sub pockets support further sub pockets almost indefinitely and changes propagate and are stored in the base pocket.

![alt text][logo]

Since Smeagol (Later known as Gollum) stores his "Precious" in a pocket most of the time The storage objects used will be called Pockets. They used to be "Register" but when we took the library out of Opinicus and decided to call it libSmeagol this made even less sense than it did before. Especially since we are saving data not to share but just to keep safe for use in the same component.

You create a storage object that saves to file:
```python
    pocket = NonVolatilePocket("some_json_file.json")
    pocket.set("data", "My Precious!")
```
Changes to a subPocket are stored in the base pocket:
```python
    sub_pocket = pocket.getAsSubPocket("extruder_1")
    sub_pocket.set("primed", False)
```
And will result in a formatted/sorted json file with a contents/structure like this:
```json
    {
        "data": "My Precious!",
        "extruder_1":
        {
            "primed": false
        }
    }
```
[logo]: images/icon.png "My Precious!"
