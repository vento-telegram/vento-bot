import abc
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

Entity = TypeVar("Entity", bound=Any)
MapperModel = TypeVar("MapperModel", bound=Any)


class DataMapperNotSetError(Exception):
    """Raise it if DataMapper class for repository not set"""


class DataMapper(Generic[Entity, MapperModel], ABC):
    @abstractmethod
    def model_to_entity(self, instance: MapperModel) -> Entity:
        pass


class AbcRepo(Generic[Entity], metaclass=abc.ABCMeta):
    """An interface for a generic repository"""

    _mapper_class: type[DataMapper[Entity, Any]]

    @property
    def data_mapper(self) -> DataMapper:
        if not self._mapper_class:
            raise DataMapperNotSetError
        return self._mapper_class()

    def map_model_to_entity(self, instance: Any) -> Entity:
        return self.data_mapper.model_to_entity(instance)
