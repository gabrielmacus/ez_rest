import pytest
from ez_rest.modules.query.services import QueryServices

  "name eq 'John' or name eq 'Jane' and surname eq 'Doe'"

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