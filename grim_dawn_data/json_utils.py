from typing import Dict, Any
import json

_JSON_CLASS_TO_TAG = {}
_JSON_TAG_TO_CLASS = {}

TYPE_FIELD = "__type__"
DATA_FIELD = "data"

class JsonSerializable:
    def __init_subclass__(cls, json_tag=None, **kwargs):
        json_tag = json_tag or cls.__name__
        if json_tag in _JSON_TAG_TO_CLASS:
            raise ValueError(f"tag `{json_tag}` is already used for type {_JSON_TAG_TO_CLASS[json_tag]}")

        _JSON_TAG_TO_CLASS[json_tag] = cls
        _JSON_CLASS_TO_TAG[cls] = json_tag

    def to_json_dict(self):
        return self.__dict__

    @classmethod
    def from_json_dict(cls, data: Dict[str, Any]):
        return cls(**data)


def serialize_json(obj):
    if isinstance(obj, JsonSerializable):
        tag = _JSON_CLASS_TO_TAG[obj.__class__]
        return {
            TYPE_FIELD: tag,
            DATA_FIELD: obj.to_json_dict()
        }

    return obj

def deserialize_json(obj):
    try:
        tag = obj[TYPE_FIELD]
    except KeyError:
        return obj

    cls = _JSON_TAG_TO_CLASS[tag]
    return cls.from_json_dict(obj[DATA_FIELD])

def load_json(path):
    with open(path, 'r') as fp:
        return json.load(fp, object_hook=deserialize_json)

def loads_json(s: str):
    return json.loads(s, object_hook=deserialize_json)

def dump_json(obj, path) -> str:
    with open(path, 'w') as fp:
        json.dump(obj, fp, default=serialize_json, indent='  ')

def dumps_json(obj: object) -> str:
    return json.dumps(obj, default=serialize_json, indent='  ')
