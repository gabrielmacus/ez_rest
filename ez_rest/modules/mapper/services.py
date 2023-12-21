from typing import Type, Callable, TypeVar, Dict
from ..singleton.models import SingletonMeta

S = TypeVar("S")
T = TypeVar("T")

class MapperServices(metaclass=SingletonMeta):
    
    _map_fn:dict = {}
    
    def register(self, 
                 source_type:Type[S], 
                 target_type:Type[T],
                 map_fn:Callable[[dict],dict]):
        self._map_fn[f'{source_type.__name__}__{target_type.__name__}'] = map_fn

    def map_dict(self,
                 source:(S|dict),
                 target_type:Type[T],
                 source_type:Type[S] = None
                 ):
        if isinstance(source, dict) and source_type is None:
             raise Exception('Source type should be specified for mapping dicts')
        elif not isinstance(source, dict):
             source_type = source.__class__
        
        data = source if isinstance(source,dict) else source.__dict__
        result:dict = self._map_fn[f'{source_type.__name__}__{target_type.__name__}'](data)
        return result

    def map(self,
                source:(S|dict),
                target_type:Type[T],
                source_type:Type[S] = None
                ) -> T:
        if isinstance(source, dict) and source_type is None:
             raise Exception('Source type should be specified for mapping dicts')
        elif not isinstance(source, dict):
             source_type = source.__class__

        data = self.map_dict(source,target_type)
        result = target_type(**data)
        return result

mapper_services = MapperServices()