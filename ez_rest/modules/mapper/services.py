from typing import Type, Callable, TypeVar, Dict
from ..singleton.models import SingletonMeta
from pydantic import BaseModel, TypeAdapter
from .exceptions import InvalidFieldException, MappingNotFoundException

class MapperServices(metaclass=SingletonMeta):
    
     _map_fn:dict = {}
    
     def register(self, 
                 source_type:Type[S], 
                 target_type:Type[T],
                 mappings:dict[str, Callable[[dict[str,any]], any]] = None):
        self._map_fn[f'{source_type.__name__}__{target_type.__name__}'] = mappings
     
     def execute_mappings(self,
               data:dict[str, any],
               mappings:dict[str, Callable[[dict[str,any]], any]]) -> dict[str, any]:
          """Executes mapping function for each field
          
          Args:
              data (dict[str, any]): Data to map
              mappings (dict[str, Callable[[dict[str,any]], any]]): Dictionary 
              of functions to map values with field name as key
          
          Example:
          .. code-block:: python
          execute_mappings({
               "name":"John",
               "surname":"Doe"
          },
          {
               "fullname":lambda src: f"{src['name']} {src['surname']}"
          })
          result = {"fullname":"John Doe"}

          Returns:
              dict[str, any]: Mapped data
          """
          mapped_data = {}
          for key in mappings:
              fn = mappings[key]
              mapped_data[key] = fn(data)
          return mapped_data
          
     def map_default(self,
                    source:dict[str, any],
                    target:dict[str, any],
                    target_type:Type[T]) -> dict[str, any]:
          """Maps fields that are shared between target model
          and source model, and are set in source dict
          but not set in target dict

          Args:
              source (dict[str, any]): Source data
              target (dict[str, any]): Target data
              target_type (Type[T]): Type to compare fields with source 
              data and map shared fields

          Returns:
              dict[str, any]: Dict with fields corresponding to
              target type
          """
          for field in target_type.model_fields:
               if field not in target and field in source:
                   target[field] = source[field] 
          return target
     
     def map_dict[S, T:BaseModel](self,
                 source:(S|dict),
                 target_type:Type[T],
                 source_type:Type[S] = None
                 ) -> dict[str, any]:
          """Maps dict or object to a dict
          with fields corresponding to the given target type

          Args:
              source (S | dict): Data to be mapped
              target_type (Type[T]):Target type to transform source data
              source_type (Type[S], optional): Type of source data
              to map. Should be specified if the source data is dict. Defaults to None.

          Raises:
              ValueError: If source_type is None and source data is dict
              MappingNotFoundException: If mapping isn't registered

          Returns:
              dict[str, any]: Mapped data
          """
          if isinstance(source, dict) and source_type is None:
             raise ValueError('Source type should be specified for mapping dicts')
          elif not isinstance(source, dict):
             source_type = source.__class__
        
          data = source if isinstance(source,dict) else source.__dict__
          map_key = f'{source_type.__name__}__{target_type.__name__}'

          if map_key not in self._map_fn:
              raise MappingNotFoundException(map_key)
          
          result:dict = self._map_fn[map_key](data)

          return result

     def map[S, T:BaseModel](self,
                source:(S|dict),
                target_type:Type[T],
                source_type:Type[S] = None
                ) -> T:
          """Maps dict or object to an object
          of the given target type

          Args:
              source (S | dict): Data to be mapped
              target_type (Type[T]): Target type to transform source data
              source_type (Type[S], optional): Type of source data
              to map. Should be specified if the source data is dict. Defaults to None.

          Returns:
              T: Mapped object
          """
          
          data = self.map_dict(source,target_type, source_type)
          data = self.map_default(source, data, target_type)
          result = target_type(**data)
          return result

mapper_services = MapperServices()