from pydantic_core import PydanticUndefined
from app.config import Config


if __name__ == "__main__":
    for key, field in Config.model_fields.items():
        if field.default is PydanticUndefined:
            value = ""
        else:
            value = field.default
        print(f"{key}={value}")
