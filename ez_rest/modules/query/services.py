from sqlalchemy import or_, and_
import re

#  "name eq 'John' and (name eq 'A' or (name eq 'B' or name eq 'Z')) or name eq 'Jane' and surname eq 'Doe'"


class QueryServices:
    
    def get_queries(self, query:str, members:dict = None):
        if members is None:
            members = {}

        pattern = r'\(([^()]+)\)'
        matches = re.finditer(pattern, query)

        query_arr = list(query)
        # The length of the query changes as members are replaced
        # by references ({number}, so an offset is declared
        # to make further replacements
        offset = 0
        index = len(members.keys())
        for match in matches:
            start = match.span()[0] - offset
            end = match.span()[1] - offset

            key = '{'+str(index)+'}'
            query_arr[start:end] = key
            offset = len(match.group()) - len(key)
            members[index] = match.group(1)
            index += 1

        new_query = "".join(query_arr)
        
        if(new_query != query):
            return self.get_queries(new_query, members)
        
        # If last member has only a member reference, it means that
        # the original query was inside brackets.
        # In that case, this member is ignored.
        if re.match(r'^{[0-9]{1,}}$', new_query) is None:
            members[index] = new_query

        return members
        
    