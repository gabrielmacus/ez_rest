from sqlalchemy import or_, and_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import column, ColumnElement
from typing import TypeVar, List, Type, Callable
from .exceptions import InvalidOperatorException,InvalidOperationException
import re
import operator
from .models import Operator


TModel = TypeVar("TModel", bound=DeclarativeBase)

QueryValue = str | int | float | ColumnElement[bool]
QueryValueList = List[QueryValue]

class QueryServices:
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
        """Gets main query and subqueries (queries between parentheses) 
        with references.

        Example: 
        .. code-block:: python
            query = "(age gte 18 or role eq 'Admin') and (age lt 18 and role ne 'Admin')"
            result = {
                    0:"age gte 18 or role eq 'Admin'",
                    1:"age lt 18 or role ne 'Admin'",
                    2:"{0} and {1}"
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
        # the original query was between parentheses.
        # In that case, this member is ignored.
        if re.match(r'^{[0-9]{1,}}$', new_query) is None:
            queries[index] = new_query

        return queries
         
    def get_operation(self,
                        operation:str,
                        translated_subqueries:dict[int, ColumnElement[bool]]) -> ColumnElement[bool]:
        """Translates operation to SqlAlchemy operation or,
        if a reference ({number}) is present, it's replaced
        by the referenced query.

        Example:
        .. code-block:: python
        get_operation("name eq 'John'",{})
        get_operation("{0}",{0:"Name eq 'John'1:"{0}"})

        Args:
            operation (str): Operation string or subquery reference
            translated_subqueries (dict[int, ColumnElement[bool]]): Already
            translated subqueries to replace references

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        reference_match = re.match(r'{([0-9]{1,})}', operation)
        if reference_match is None:
            return self.translate_operation(operation)
        else:
            reference = int(reference_match.group(1))
            return translated_subqueries[reference]
    
    def translate_subquery( self,
                        subquery:str,
                        translated_subqueries:dict[int, str]) -> ColumnElement[bool]:
        """Translates subquery string (query between parentheses)
        to SqlAlchemy query.
        
        Args:
            subquery (str): Subquery to be translated
            translated_subqueries (dict[int, str]): Dictionary
            with already translated subqueries, so references
            can be repaced ({number})

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        parsed_members:List[ColumnElement[bool]] = []
        members = self.get_members(subquery)
        for member in members:
            
            parsed_operations:List[ColumnElement[bool]] = []
            for op in member:
                parsed_operations.append(
                    self.get_operation(op, translated_subqueries)
                )
            parsed_members.append(and_(*parsed_operations))
        return or_(*parsed_members)

    def translate_query(
            self,
            query:str) -> ColumnElement[bool]:
        """Translates complete query string into SqlAlchemy query

        Args:
            query (str): Query to be translated

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        queries = self.get_queries(query)
        translated_subqueries = {}

        for query_reference in queries:
            subquery = queries[query_reference]
            translated_subqueries[query_reference] = self.translate_subquery(
                subquery, 
                translated_subqueries)
        return and_(translated_subqueries[query_reference])

    def translate_operation(self, 
                        operation: str) -> ColumnElement[bool]:
        """Translates operation string into SqlAlchemy operation to
        be used in a query
        
        Example:
        .. code-block:: python
        translate_operation("name eq 'John'")
        translate_operation("age gte 18")

        Args:
            operation (str): Operation string to be translated

        Raises:
            InvalidOperationException: if the string isn't well formed
            InvalidOperatorException: if the comparison operator isn't supported

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        operation_pattern = r'^([^ ]+) ([^ ]+) (.*)$'
        matches = re.findall(operation_pattern, operation)

        if len(matches) == 0:
            raise InvalidOperationException(f"Operation: '{operation}'")

        attr:str = matches[0][0]
        op:str = matches[0][1]
        value:str = str(matches[0][2])
        parsed_value = self.parse_value(value)

        try:
            return self.parse_operation(
                attribute=attr,
                operator=Operator[op.upper()],
                value=parsed_value
            )
        except KeyError:
            raise InvalidOperatorException(f"Invalid operator: {op}")

    def parse_value(self, 
                    value:str) -> QueryValue | QueryValueList:
        """Parses value to be used in query.

        Example:
        .. code-block:: python
        'John Doe' # Parsed as string
        10 # Parsed as int
        10.5 # Parsed as float
        ['John', 'Jane'] # Parsed as List[str]
        middlename # Parsed as ColumnElement[bool]
        # and so on...


        Args:
            value (str): Value to be parsed

        Returns:
            QueryValue | QueryValueList: Parsed value
        """
        value = value.strip()
        if value.startswith("'") and value.endswith("'"):
            parsed_value = value \
                .removeprefix("'") \
                .removesuffix("'")
        elif value.startswith("[") and value.endswith("]"):
            parsed_value = value \
                .removeprefix("[") \
                .removesuffix("]") \
                .split(",")
            parsed_value = [self.parse_value(v) for v in parsed_value]
        elif re.match(r'^[0-9]+$', value) == None:
            parsed_value = column(value)
        elif '.' in value:
            parsed_value = float(value)
        else:
            parsed_value = int(value)
        return parsed_value
             
    def parse_operation(self, 
                        operator:Operator,
                        attribute:str,
                        value:any) -> ColumnElement[bool]:
        """
        Transform an attribute, operator and value
        into an SqlAlchemy operation to be used
        in a query

        Args:
            operator (Operator): Comparison operator
            attribute (str): Attribute from model
            value (any): Comparison value

        Returns:
            ColumnElement[bool]: Element to be used in SqlAlchemy query
        """

        ops:dict[str, 
                    Callable[[str,any], 
                    ColumnElement[bool]]] = {
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

        return ops[operator](attribute,value)
    
