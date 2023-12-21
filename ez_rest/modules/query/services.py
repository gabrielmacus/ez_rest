from sqlalchemy import or_, and_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import column, ColumnElement, ColumnClause, func, UnaryExpression
from typing import TypeVar, List, Type, Callable
from .exceptions import InvalidOperatorException,InvalidOperationException,InvalidFieldsException,InvalidOrderByClauseException
import regex as re
import operator
from .models import Operator, Functions, Query

TModel = TypeVar("TModel", bound=DeclarativeBase)

QueryValue = str | int | float | ColumnElement[bool]
QueryValueList = List[QueryValue]

class QueryServices:
    def get_members(self, 
                    group:str) -> List[List[str]]:
        """Gets members of a group of operations. Example:
        .. code-block:: python
            group = "age ge 18 and role eq 'Admin' or name eq 'John' and surname eq 'Doe'"
            
            result = [
                ["age ge 18", "role eq 'Admin'"],
                ["name eq 'John'","surname eq 'Doe'"]
            ]

        Args:
            group (str): Group to get members from

        Returns:
            List[List[str]]: Array of members
        """
        
        members = group.split(" or ")
        for index, member in enumerate(members):
            members[index] =  member.split(" and ")
        
        return members
    
    def get_functions(self,
                    query:str):
        pattern = r"([a-zA-Z]+)\(([0-9a-zA-Z' ,]+)\)"
        matches = re.finditer(pattern, query)
        for match in matches:
            print(match.group())

    def get_groups(self, 
                    query:str, 
                    groups:dict[int,str] = None) -> dict[int,str]:
        """Gets groups of operations

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
            groups (dict[str,str], optional): Accumulated groups. Defaults to None.

        Returns:
            dict[str,str]: Dict of groups
        """
        if groups is None:
            groups = {}

        pattern = r'\(([^()]+)\)'
        matches = re.finditer(pattern, query)

        new_query = query
        index = len(groups.keys())
        for match in matches:
            match_start = match.span()[0]
            # Checks if prev char of match is next to parentheses
            # to determine if corresponds to a function
            if match_start == 0 or \
               re.match(r'[A-Z]',query[match_start - 1]) is None:
                key = '{'+str(index)+'}'
                new_query = new_query \
                    .replace(match.group(0),
                             key, 
                             1)
                groups[index] = match.group(1)
                index += 1
            else:
                new_query = new_query \
                    .replace(match.group(0),
                             f'{{{match.group(1)}}}', 
                             1)

        if(new_query != query):
            return self.get_groups(new_query, groups)
        
        # If last member has only a member reference, it means that
        # the original query was between parentheses.
        # In that case, this member is ignored.
        if re.match(r'^{[0-9]{1,}}$', new_query) is None:
            groups[index] = new_query

        return groups
         
    def get_operation(self,
                        operation:str,
                        translated_groups:dict[int, ColumnElement[bool]]) -> ColumnElement[bool]:
        """Translates operation to SqlAlchemy operation or,
        if a reference ({number}) is present, it's replaced
        by the referenced group of operations.

        Example:
        .. code-block:: python
        get_operation("name eq 'John'",{})
        get_operation("{0}",{0:"Name eq 'John'1:"{0}"})

        Args:
            operation (str): Operation string or subquery reference
            translated_groups (dict[int, ColumnElement[bool]]): Already
            translated groups to replace references

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        reference_match = re.match(r'{([0-9]{1,})}', operation)
        if reference_match is None:
            return self.translate_operation(operation)
        else:
            reference = int(reference_match.group(1))
            return translated_groups[reference]
    
    def translate_group( self,
                        group:str,
                        translated_groups:dict[int, str]) -> ColumnElement[bool]:
        """Translates group of operations
        to SqlAlchemy query.
        
        Args:
            group (str): Group of operations to be translated
            translated_groups (dict[int, str]): Dictionary
            with already translated groups, so references
            can be repaced ({number})

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        parsed_members:List[ColumnElement[bool]] = []
        members = self.get_members(group)

        for member in members:
            
            parsed_operations:List[ColumnElement[bool]] = []
            for op in member:
                parsed_operations.append(
                    self.get_operation(op, translated_groups)
                )
            parsed_members.append(and_(*parsed_operations))
        return or_(*parsed_members)

    def translate_query(
            self,
            query:str) -> ColumnElement[bool]:
        """Translates query string into SqlAlchemy query

        Args:
            query (str): Query to be translated

        Returns:
            ColumnElement[bool]: SqlAlchemy query
        """
        groups = self.get_groups(query)
        translated_groups = {}

        for group_reference in groups:
            group = groups[group_reference]
            translated_groups[group_reference] = self.translate_group(
                group, 
                translated_groups)
        
        return and_(translated_groups[group_reference])

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

        value1:str = matches[0][0]
        op:str = matches[0][1]
        value2:str = str(matches[0][2])
        parsed_value1 = self.parse_value(value1)
        parsed_value2 = self.parse_value(value2)

        try:
            return self.parse_operation(
                operator=Operator[op.upper()],
                value1=parsed_value1,
                value2=parsed_value2
            )
        except KeyError:
            raise InvalidOperatorException(f"Invalid operator: {op}")
    
    def translate_function(self,
                            fn_name:str,
                            args:str):

        fn_args_matches = re.finditer(r'{(?:[^{}]+|(?R))*+}', args)
        fn_args_replacements = []
        for match in fn_args_matches:
            fn_args = match.group()
            args = args.replace(fn_args, f"[args_{len(fn_args_replacements)}]",1)
            fn_args_replacements.append(fn_args)
            
        split_args = [arg for arg in args.split(',')]
        for index, replacement in enumerate(fn_args_replacements):
            for index2, arg in enumerate(split_args):
                split_args[index2] = arg.replace(f"[args_{index}]",replacement,1)
        
        parsed_args = [self.parse_value(a) for a in split_args]

        fns = {
            Functions.EXTRACT:lambda : func.extract(*parsed_args),
            Functions.SUM:lambda : parsed_args[0] + parsed_args[1],
            Functions.SUB:lambda : parsed_args[0] - parsed_args[1],
            Functions.DIV:lambda : parsed_args[0] / parsed_args[1],
            Functions.MUL:lambda : parsed_args[0] * parsed_args[1]
        }

        return fns[Functions[fn_name.upper()]]()

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

        fn_pattern = r'([a-zA-Z0-9_]+){(.*)}'
        column_pattern = r'^[0-9]+$'
        
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
        elif re.match(fn_pattern, value) is not None: # Parses function
            fn_match = re.match(fn_pattern, value)
            parsed_value = self.translate_function(
                fn_match.group(1),
                fn_match.group(2)
            )
        elif re.match(column_pattern, value) is None:
            parsed_value = column(value)
        elif '.' in value:
            parsed_value = float(value)
        else:
            parsed_value = int(value)
        return parsed_value

    def parse_operation(self, 
                        operator:Operator,
                        value1:any,
                        value2:any) -> ColumnElement[bool]:
        """
        Transform an attribute, operator and value
        into an SqlAlchemy operation to be used
        in a query

        Args:
            operator (Operator): Comparison operator
            value1 (any): Comparison value
            value2 (any): Comparison value

        Returns:
            ColumnElement[bool]: Element to be used in SqlAlchemy query
        """
        ops:dict[str, 
                    Callable[[str,any], 
                    ColumnElement[bool]]] = {
            Operator.GT: lambda: value1 > value2,
            Operator.LT: lambda : value1 < value2,
            Operator.GE: lambda : value1 >= value2,
            Operator.LE: lambda : value1 <= value2,
            Operator.EQ: lambda : value1 == value2,
            Operator.NE: lambda : value1 != value2,
            Operator.IN: lambda : value1.in_(value2),
            Operator.NIN: lambda : value1.not_in(value2),
            Operator.LK: lambda : value1.like(value2),
            Operator.ILK: lambda : value1.ilike(value2),
            Operator.NLK: lambda : value1.not_like(value2),
            Operator.NILK: lambda : value1.not_ilike(value2)
        }

        return ops[operator]()
    
    def translate_order_by(self,
                           order_by:str) -> List[UnaryExpression]:
        order_by = order_by.strip()
        pattern = r'^([a-zA-Z0-9_]+) (desc|asc|DESC|ASC)$'
        columns = order_by.split(',')
        
        translated_expressions:List[UnaryExpression] = []
        for col in columns:
            col = col.strip()
            match = re.match(pattern, col)

            if match is None:
                raise InvalidOrderByClauseException(f"Invalid column: {col}")
            
            col = column(match.group(1))
            translated_expression = col.desc()
            if match.group(2).upper() == 'ASC':
                translated_expression = col.asc()
                
            translated_expressions.append(translated_expression)
            
        return translated_expressions
    
    def translate_fields(self,
                         fields:str) -> List[str]:
        fields_list = [f.strip() for f in fields.split(',')]
        fields_columns:List[str] = []
        for field in fields_list:
            if re.match(r'^[a-zA-Z_0-9]+$', field) is None:
                raise InvalidFieldsException(f"Invalid field: {field}")
            fields_columns.append(field)
        return fields_columns


    def handle_query(self, 
                        page:int,
                        limit:int,
                        filter:str = None,
                        order_by:str = None,
                        fields:str = None) -> Query:
        filter_query = None
        if filter not in (None, ""):
            filter_query = self.translate_query(filter)
        
        order_by_query = None
        if order_by not in (None, ""):
            order_by_query = self.translate_order_by(order_by)
        
        fields_query = None
        if fields not in (None, ""):
            fields_query = self.translate_fields(fields)
        
        return Query(
            filter=filter_query,
            limit=limit,
            page=page,
            order_by=order_by_query,
            fields=fields_query
        )
        