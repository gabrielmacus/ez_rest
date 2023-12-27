from typing import Type, Callable, TypeVar, Dict
from ..singleton.models import SingletonMeta
from pydantic import BaseModel, TypeAdapter
from .exceptions import InvalidFieldException, MappingNotFoundException
from .models import IgnoredAttr
import re

class MapperServices(metaclass=SingletonMeta):

    _map_fn:dict = {}

    def register[S, T](self, 
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
            mappings (dict[str, Callable[[dict[str,any]], any]]|str): Dictionary 
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
            
            mapped_value = fn(data)
            
            if type(mapped_value) is IgnoredAttr:
                continue
            mapped_data[key] = mapped_value
            
        return mapped_data

    '''
    def parse_mapping(self, 
                      value:str,
                      data:dict[str, any]):
        if re.match(r'^[a-zA-Z_0-9]+$', value):
            return data[value]
        
        for key in data:
            if data[key] is None : continue
            value = value.replace(f"{{{key}}}", str(data[key]))
            
        return re.sub(r'(\{[a-zA-Z_0-9]+\})',"", value).strip()
    '''

    def map_default[T](self,
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
        # Merges target and target parent fields
        fields = target_type.__base__.__annotations__.copy()
        fields.update(target_type.__annotations__)
        
        for field in fields:
            if field not in target and field in source:
                target[field] = source[field] 
        return target
    
    def map_dict[T, S](self,
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
        
        result:dict = self.execute_mappings(data, self._map_fn[map_key])
        result = self.map_default(data, result, target_type)

        return result

    def map[S, T](self,
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
        result = target_type(**data)
        return result

mapper_services = MapperServices()