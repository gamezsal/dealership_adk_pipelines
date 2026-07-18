from fastapi.encoders import jsonable_encoder

class DictWithListIter(dict):
    def __iter__(self):
        return iter(self.values())

data = DictWithListIter()
data["default"] = {"name": "default", "type": "adk"}

# Test iteration
print("Iteration values:")
for val in data:
    print(val)

# Test jsonable_encoder
encoded = jsonable_encoder(data)
print(f"Encoded: {encoded} (type: {type(encoded)})")
