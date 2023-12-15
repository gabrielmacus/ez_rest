from sqlalchemy import or_, and_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import column, ColumnElement
from typing import TypeVar, List, Type, Callable
from .exceptions import InvalidOperatorException,InvalidOperationException
import re
import operator
from .models import Operator


TModel = TypeVar("TModel", bound=DeclarativeBase)

class QueryServices:
    
    def get_operation(self,
                        operation:str,
                        parsed_queries:dict[int, ColumnElement[bool]]) -> ColumnElement[bool]:
        reference_match = re.match(r'{([0-9]{1,})}', operation)
        if reference_match is None:
            return self.parse_operation(operation)
        else:
            reference = int(reference_match.group(1))
            return parsed_queries[reference]
    
    def parse_subquery( self,
                        subquery:str,
                        parsed_queries:dict[int, str]) -> ColumnElement[bool]:
        parsed_members:List[ColumnElement[bool]] = []
        members = self.get_members(subquery)
        for member in members:
            
            parsed_operations:List[ColumnElement[bool]] = []
            for op in member:
                parsed_operations.append(
                    self.get_operation(op, parsed_queries)
                )
            parsed_members.append(and_(*parsed_operations))
        return or_(*parsed_members)

    def parse_query(
            self,
            query:str) -> ColumnElement[bool]:
        
        queries = self.get_queries(query)
        parsed_queries = {}
        for query_reference in queries:
            query = queries[query_reference]
            parsed_queries[query_reference] = self.parse_subquery(
                query, 
                parsed_queries)
        return and_(parsed_queries[query_reference])

    def parse_value(self, 
                    value:str) -> str | int | float | List[str] | List[int] | List[float]:
        value = value.strip()
        if value.startswith("'") and value.endswith("'"):
            return value.removeprefix("'").removesuffix("'")
        elif value.startswith("[") and value.endswith("]"):
            parsed_value = value \
                .removeprefix("[") \
                .removesuffix("]") \
                .split(",")
            return [self.parse_value(v) for v in parsed_value]
        elif '.' in value:
            return float(value)
        else:
            return int(value)

    def parse_operation(self, 
                     operation: str) -> ColumnElement[bool]:
        operation_pattern = r'(.*) (gt|lt|ge|le|eq|ne|in|nin|lk|ilk|nlk|nilk) (.*)'
        matches = re.findall(operation_pattern, operation)

        if len(matches) == 0:
            raise InvalidOperationException(f"Operation: '{operation}'")

        attr:str = matches[0][0]
        op:str = matches[0][1]
        value:str = str(matches[0][2])
        parsed_value = self.parse_value(value)

        return self._parse_operation(
            attribute=attr,
            operator=Operator[op.upper()],
            value=parsed_value
        )

    def parse_operator(attr:str, value):
        
    def _parse_operation(self, 
                        operator:Operator,
                        attribute:str,
                        value:str | int | float | List[str] | List[int] | List[float]) -> ColumnElement[bool]:
        op = operator
        attr = attribute

        ops:dict[str, Callable[[str,any], ColumnElement[bool]]] = {
            Operator.GT: lambda attr,value: column(attr) > value,
            Operator.LT: lambda attr,value: column(attr) < value,
            Operator.GE: lambda attr,value: column(attr) >= value,
            Operator.LE: lambda attr,value: column(attr) <= value,
            Operator.EQ: lambda attr,value: column(attr) == value,
            Operator.NE: lambda attr,value: column(attr) != value,
            Operator.IN: lambda attr,value: column(attr).in_(value),
            Operator.NIN: lambda attr,value: column(attr).not_in(value),
            Operator.LK: lambda attr,value: column(attr).like(value),
            Operator.ILK: lambda attr,value: column(attr).ilike(value),
            Operator.NLK: lambda attr,value: column(attr).not_like(value),
            Operator.NILK: lambda attr,value: column(attr).not_ilike(value)
        }
        return ops[op](attr, value)
        '''
        parsed_operation:ColumnElement[bool]
        if op == Operator.GT:
            parsed_operation =  column(attr) > value
        elif op == Operator.LT:
            parsed_operation =  column(attr) < value
        elif op == Operator.GE:
            parsed_operation =  column(attr) >= value
        elif op == Operator.LE:
            parsed_operation =  column(attr) <= value
        elif op == Operator.EQ:
            parsed_operation =  column(attr) == value
        elif op == Operator.NE:
            parsed_operation =  column(attr) != value
        elif op == Operator.IN:
            parsed_operation =  column(attr).in_(value)
        elif op == Operator.NIN:
            parsed_operation =  column(attr).not_in(value)
        elif op == Operator.LK:
            parsed_operation =  column(attr).like(value)
        elif op == Operator.ILK:
            parsed_operation =  column(attr).ilike(value)
        elif op == Operator.NLK:
            parsed_operation =  column(attr).not_like(value)
        elif op == Operator.NILK:
            parsed_operation =  column(attr).not_ilike(value)
        else:
            raise InvalidOperatorException(f"Operator {op} not recognized. Value: {value}")
    
        return parsed_operation
        '''

    def get_members(self, 
                    query:str) -> List[List[str]]:
        """Gets query members. Example:
        .. code-block:: python
            query = "age ge 18 and role eq 'Admin' or name eq 'John' and surname eq 'Doe'"
            
            result = [
                ["age ge 18", "role eq 'Admin'"],
                ["name eq 'John'","surname eq 'Doe'"]
            ]

        Args:
            query (str): Query to get members from

        Returns:
            List[List[str]]: Array of members
        """
        
        members = query.split(" or ")
        for index, member in enumerate(members):
            members[index] =  member.split(" and ")
        
        return members

    def get_queries(self, 
                    query:str, 
                    queries:dict[int,str] = None) -> dict[int,str]:
        """Gets main query and subqueries (queries in brackets) with references.
        Example: 
        .. code-block:: python
            query = "(age gte 18 and role eq 'Admin') or (age lt 18 and role ne 'Admin')"
            result = {
                    0:"age gte 18 and role eq 'Admin'",
                    1:"age lt 18 and role ne 'Admin'",
                    2:"{0} or {1}"
                }
        Args:
            query (str): Main query
            queries (dict[str,str], optional): Accumulated queries. Defaults to None.

        Returns:
            dict[str,str]: Dict with main query and subqueries with references
        """
        if queries is None:
            queries = {}

        pattern = r'\(([^()]+)\)'
        matches = re.finditer(pattern, query)

        query_arr = list(query)
        # The length of the query changes as members are replaced
        # by references ({number}, so an offset is declared
        # to make further replacements
        offset = 0
        index = len(queries.keys())
        for match in matches:
            start = match.span()[0] - offset
            end = match.span()[1] - offset

            key = '{'+str(index)+'}'
            query_arr[start:end] = key
            offset = len(match.group()) - len(key)
            queries[index] = match.group(1)
            index += 1

        new_query = "".join(query_arr)
        
        if(new_query != query):
            return self.get_queries(new_query, queries)
        
        # If last member has only a member reference, it means that
        # the original query was inside brackets.
        # In that case, this member is ignored.
        if re.match(r'^{[0-9]{1,}}$', new_query) is None:
            queries[index] = new_query

        return queries
        
    