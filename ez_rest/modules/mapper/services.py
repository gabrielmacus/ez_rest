from typing import Type, Callable, TypeVar, Dict

S = TypeVar("S")
T = TypeVar("T")

class MapperServices:
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
    
    _map_fn:dict = {}
    
    def register[S,T](self, 
                 source_type:Type[S], 
                 target_type:Type[T],
                 map_fn:Callable[[S],T]):
        self._map_fn[f'{source_type.__name__}__{target_type.__name__}'] = map_fn

    def map[S,T](self,
                source:S,
                target_type:Type[T]
                ) -> T:
        result:T = self._map_fn[f'{source.__class__.__name__}__{target_type.__name__}'](source)
        return result

mapper_services = MapperServices()