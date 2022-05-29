from pathlib import Path
from typing import Type, TypeVar

from bevy import Dependencies
from bevy.function_provider import FunctionProvider
from pydantic import BaseSettings as _BaseSettings, Extra
from yaml import safe_load


class BaseSettingsModel(_BaseSettings):
    class Config:
        extra = Extra.allow
        env_prefix = "SOC_"


T = TypeVar("T", bound=BaseSettingsModel)


class Config(Dependencies):
    default_paths = ("production.config.yaml", "development.config.yaml")

    def __init__(self, *file_paths: str | Path):
        super().__init__()
        self._paths = tuple(Path(file_path) for file_path in file_paths or self.default_paths)
        self._data = {}

        self._load()

    def get(self, model: Type[T], key: str = None) -> T:
        data = self._data.get(key, {}) if key else self._data
        return model(**data)

    def _load(self):
        _open = self.__bevy__.get(open, provider_type=FunctionProvider)
        for path in self._paths:
            try:
                f = _open(path, "rb")
            except FileNotFoundError:
                pass
            else:
                with f:
                    self._data |= safe_load(f.read())
