import pytest
from ez_rest.modules.query.services import QueryServices
from tests.mock_db_services import MockDbServices
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import BigInteger,String, Integer
from sqlalchemy import or_, and_, Column, create_engine


class Student(DeclarativeBase):
     id:Mapped[int] = mapped_column(BigInteger(), primary_key=True)
     name:Mapped[str] = mapped_column(String())
     age:Mapped[str] = mapped_column(Integer())

@pytest.fixture
def engine():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    return engine


def test_parse_query():
    services = QueryServices()
    #query = services.parse_query("(age ge 18 and role eq 'Admin') or (age lt 18 and role ne 'Admin')")
    query = services.parse_query("name eq 'John' or surname eq 'Doe' and (name eq 'A' or (name eq 'B' or name eq 'Z')) or name eq 'Jane' and surname eq 'Doe' and (name eq 'Foo' or name eq 'Bar')")
    print(query)
    
    assert 0 == 1

@pytest.mark.parametrize("operation, expected_query", [
    ("age ge 18", "age >= 18"),
    ("age le 18", "age <= 18"),
    ("age gt 18", "age > 18"),
    ("age lt 18", "age < 18"),
    ("name eq 'André Luís'", "name = 'André Luís'"),
    ("name eq ''André Luís''", "name = '''André Luís'''"),
    ("name ne 'André Luís'", "name != 'André Luís'"),
    ("name in [ 'André Luís', 'John Charles' ]", "name IN ('André Luís', 'John Charles')"),
    ("name in ['André Luís','John Charles']", "name IN ('André Luís', 'John Charles')"),
    ("age in [18,  19,20]", "age IN (18, 19, 20)"),
    ("age nin [18,  19,20]", "(age NOT IN (18, 19, 20))"),
    ("name lk 'André Luís'", "name LIKE 'André Luís'"),
    ("name lk '%Luís'", "name LIKE '%Luís'"),
    ("name lk 'André%'", "name LIKE 'André%'"),
    ("name lk '%Lu%'", "name LIKE '%Lu%'"),
    ("name lk 'André Luís\%'", "name LIKE 'André Luís\%'"),
    ("name ilk 'André Luís'", "lower(name) LIKE lower('André Luís')"),
    ("name ilk '%Luís'", "lower(name) LIKE lower('%Luís')"),
    ("name ilk 'André%'", "lower(name) LIKE lower('André%')"),
    ("name ilk '%Lu%'", "lower(name) LIKE lower('%Lu%')"),
    ("name ilk 'André Luís\%'", "lower(name) LIKE lower('André Luís\%')"),
    ("name nlk 'André Luís'", "name NOT LIKE 'André Luís'"),
    ("name nlk '%Luís'", "name NOT LIKE '%Luís'"),
    ("name nlk 'André%'", "name NOT LIKE 'André%'"),
    ("name nlk '%Lu%'", "name NOT LIKE '%Lu%'"),
    ("name nlk 'André Luís\%'", "name NOT LIKE 'André Luís\%'"),
    ("name nilk 'André Luís'", "lower(name) NOT LIKE lower('André Luís')"),
    ("name nilk '%Luís'", "lower(name) NOT LIKE lower('%Luís')"),
    ("name nilk 'André%'", "lower(name) NOT LIKE lower('André%')"),
    ("name nilk '%Lu%'", "lower(name) NOT LIKE lower('%Lu%')"),
    ("name nilk 'André Luís\%'", "lower(name) NOT LIKE lower('André Luís\%')"),

])
def test_parse_operation(engine, operation, expected_query):
    services = QueryServices()
    parsed_operation = services.parse_operation(operation)
    compiled_query = parsed_operation \
        .compile(engine, compile_kwargs={"literal_binds": True})
    
    print(compiled_query, expected_query)

    assert str(compiled_query) == expected_query

@pytest.mark.parametrize("query, expected_members", [
    (
        "age ge 18 and role eq 'Admin'",
        [["age ge 18", "role eq 'Admin'"]]
    ),
    (
        "age ge 18 and role eq 'Admin' or name eq 'John' and surname eq 'Doe'",
        [["age ge 18", "role eq 'Admin'"],["name eq 'John'","surname eq 'Doe'"]]
    )
])
def test_get_members(query, expected_members):
     services = QueryServices()
     members = services.get_members(query)
     print(members)
     assert members == expected_members

@pytest.mark.parametrize("query, expected_queries", [

    (
        "(age ge 18 and role eq 'Admin') or (age lt 18 and role ne 'Admin')",
        {
            0:"age ge 18 and role eq 'Admin'",
            1:"age lt 18 and role ne 'Admin'",
            2:"{0} or {1}"
        }
    ),
    (
        "(age ge 18 and role eq 'Admin') or age lt 18",
        {
            0:"age ge 18 and role eq 'Admin'",
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
        "(name eq 'André Luís' or surname eq 'Doe' and (name eq 'A' or (name eq 'B' or name eq 'Z')) or name eq 'Jane' and surname eq 'Doe' and (name eq 'Foo' or name eq 'Bar'))",
        {
            0:"name eq 'B' or name eq 'Z'",
            1:"name eq 'Foo' or name eq 'Bar'",
            2:"name eq 'A' or {0}",
            3:"name eq 'André Luís' or surname eq 'Doe' and {2} or name eq 'Jane' and surname eq 'Doe' and {1}"
        }
    )
])
def test_get_queries(query, expected_queries):
    services = QueryServices()
    queries = services.get_queries(query)
    
    assert queries == expected_queries

