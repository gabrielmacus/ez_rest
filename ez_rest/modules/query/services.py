from sqlalchemy import or_, and_
import re

class QueryServices:
    
    def get_queries(self, 
                    query:str, 
                    queries:dict[str,str] = None) -> dict[str,str]:
        """Gets main query and subqueries with references.
        Example: "(age gte 18 and role eq 'Admin') or (age lt 18 and role ne 'Admin')"
        Returns: {
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
        
    