import pytest
from ez_rest.modules.query.services import QueryServices

@pytest.mark.parametrize("query, expected_members", [

    (
        "(age gte 18 and role eq 'Admin') or (age lt 18 and role ne 'Admin')",
        {
            0:"age gte 18 and role eq 'Admin'",
            1:"age lt 18 and role ne 'Admin'",
            2:"{0} or {1}"
        }
    ),
    (
        "(age gte 18 and role eq 'Admin') or age lt 18",
        {
            0:"age gte 18 and role eq 'Admin'",
            1:"{0} or age lt 18"
        }
    ),
    (
        "name eq 'John' or surname eq 'Doe' and (name eq 'A' or (name eq 'B' or name eq 'Z')) or name eq 'Jane' and surname eq 'Doe' and (name eq 'Foo' or name eq 'Bar')",
        {
            0:"name eq 'B' or name eq 'Z'",
            1:"name eq 'Foo' or name eq 'Bar'",
            2:"name eq 'A' or {0}",
            3:"name eq 'John' or surname eq 'Doe' and {2} or name eq 'Jane' and surname eq 'Doe' and {1}"
        }
    ),
    (
        "(name eq 'John' or surname eq 'Doe' and (name eq 'A' or (name eq 'B' or name eq 'Z')) or name eq 'Jane' and surname eq 'Doe' and (name eq 'Foo' or name eq 'Bar'))",
        {
            0:"name eq 'B' or name eq 'Z'",
            1:"name eq 'Foo' or name eq 'Bar'",
            2:"name eq 'A' or {0}",
            3:"name eq 'John' or surname eq 'Doe' and {2} or name eq 'Jane' and surname eq 'Doe' and {1}"
        }
    )
])
def test_get_queries(query, expected_queries):
    services = QueryServices()
    queries = services.get_queries(query)
    
    assert queries == expected_queries

'''
@pytest.mark.parametrize("query_str,members",[
    (
        "name eq 'John' and surname eq 'Doe'", 
        ["name eq 'John'","surname eq 'Doe'"]
    ),
    (
        "(name eq 'John' or name eq 'Jane') and surname eq 'Doe'", 
        ["name eq 'John' or name eq 'Jane'","surname eq 'Doe'"]
    ),
    (
        "(name eq 'John' and surname eq 'Doe') or (name eq 'Foo' and surname eq 'bar')"
    )
          #https://stackoverflow.com/questions/68952806/sql-alchemy-orm-bracketing-and-statements-with-or-statements              
])
def test_split_filter_members(query_str, members):
    
    services = QueryServices()
    assert members == services.split_filter_members(query_str)
'''