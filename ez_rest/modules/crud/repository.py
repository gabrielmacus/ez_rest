from typing import List, TypeVar, Generic, Type
from sqlalchemy import func, select, ColumnElement, ColumnClause, and_, UnaryExpression,column
from sqlalchemy.orm import Session, load_only, undefer
from ..db.services import DbServices
from .models import BaseModel
from datetime import datetime
from abc import ABC

T = TypeVar("T", bound=BaseModel)

class BaseRepository(ABC, Generic[T]):
    _db_services:DbServices
    _model: Type[T]
    
    def __init__(self,  
                 model:Type[T], 
                 db_services:DbServices = None) -> None:
        self._db_services = DbServices() if db_services == None else db_services
        self._model = model
        
    def create(self, item:T) -> T:
        with Session(self._db_services.get_engine()) as session:
            session.add(item)
            session.commit()
            session.refresh(item)
        return item

    def read(
            self, 
            filter:ColumnElement[bool] = None,
            limit:int = None, 
            offset:int = None,
            order_by:List[UnaryExpression] = None,
            fields:List[str] = None,
            include_deleted:bool = False
            ) -> List[T]:
            
        with Session(self._db_services.get_engine()) as session:
            statement = select(self._model)

            if fields is not None:
                statement = statement.options(
                    load_only(*[getattr(self._model,f) for f in fields])
                )
                
            if filter is not None:
                statement = statement.where(filter)

            if include_deleted == False:
                statement = statement \
                    .where(self._model.deleted_at == None)

            statement = statement \
                .limit(limit) \
                .offset(offset)
            
            if order_by is not None:
                statement = statement \
                    .order_by(*order_by)

            results = session.execute(statement)
            items = results.scalars().all()
        return items
    
    def readById(
            self,
            id:int,
            include_deleted:bool = False
            ) -> T:
        with Session(self._db_services.get_engine()) as session:
            statement = select(self._model) \
                        .where(self._model.id == id)

            if include_deleted == False:
                statement = statement \
                    .where(self._model.deleted_at == None)
                        
            results = session.execute(statement)
            item = results.scalar_one_or_none()
        return item
    
    def updateById(self,partial_data:dict, id:int):
        with Session(self._db_services.get_engine()) as session:            
            statement = select(self._model).where(self._model.id == id)
            item = session.execute(statement).scalar_one()
            item.updated_at = datetime.utcnow()
            
            for key in partial_data:
                value = partial_data[key]
                if key == "id" : continue
                setattr(item, key, value)

            session.add(item)
            session.commit()
            session.refresh(item)
        
        return item

    def deleteById(self, id:int, soft_delete:bool = True):
        with Session(self._db_services.get_engine()) as session:
            statement = select(self._model).where(self._model.id == id)
            item = session.execute(statement).scalar_one()
            
            if soft_delete:
                item.deleted_at = datetime.utcnow()
                session.add(item)
            else:
                session.delete(item)
            session.commit()

    def count(self, 
            filter:ColumnElement[bool] = None,
            include_deleted:bool = False) -> int:
        
        with Session(self._db_services.get_engine()) as session:
            statement = session\
                .query(func.count(self._model.id))
            
            if filter is not None:
                statement = statement.where(filter)
                
            if include_deleted == False:
                statement = statement.where(self._model.deleted_at == None)

            count_result = statement.scalar()
            
        return count_result
        
