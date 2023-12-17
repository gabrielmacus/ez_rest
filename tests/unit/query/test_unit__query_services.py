import pytest
from ez_rest.modules.query.services import QueryServices
from ez_rest.modules.query.exceptions import InvalidOperatorException
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

@pytest.mark.parametrize("query, expected_query", [
    (
        f"name lk '%John%' and ((age ge 18 or surname eq 'Doe') or (age lt 18 or surname eq 'Foobar'))",
        "name LIKE '%John%' AND (age >= 18 OR surname = 'Doe' OR age < 18 OR surname = 'Foobar')"
    ),
    (
        f"name lk '%John%' and ((age ge 18 and surname eq 'Doe') or (age lt 18 and surname eq 'Foobar'))",
        "name LIKE '%John%' AND (age >= 18 AND surname = 'Doe' OR age < 18 AND surname = 'Foobar')"
    ),
    (
        f"name lk '%John%' and (age ge 18 or address ilk '%Alton Road%' and surname eq 'Bar') and (age ge 18 or address ilk '%Leland Road%' and surname eq 'Bar')",
        "name LIKE '%John%' AND (age >= 18 OR lower(address) LIKE lower('%Alton Road%') AND surname = 'Bar') AND (age >= 18 OR lower(address) LIKE lower('%Leland Road%') AND surname = 'Bar')"
    ),
    (
        f"name eq 'John' and surname eq 'Doe'",
        "name = 'John' AND surname = 'Doe'"
    ),
    (
        f"name eq 'John'",
        "name = 'John'"
    ),
    (
        f"name eq middlename or birthdate ge '1996-01-01'",
        "name = middlename OR birthdate >= '1996-01-01'"
    ),
    (
        f"name eq middlename or EXTRACT('year',birthdate) ge 1996",
        "name = middlename OR CAST(STRFTIME('%Y', birthdate) AS INTEGER) >= 1996"
    ),
    (
        "SUB(2023,EXTRACT('year',birthdate)) ge 50",
        "2023 - CAST(STRFTIME('%Y', birthdate) AS INTEGER) >= 50"
    ),
    (
        "MUL(SUB(2023,EXTRACT('year',birthdate)),2) ge 50",
        "(2023 - CAST(STRFTIME('%Y', birthdate) AS INTEGER)) * 2 >= 50"
    )
])
def test_translate_query(engine, query, expected_query):
    services = QueryServices()
    #query = services.parse_query("(age ge 18 and role eq 'Admin') or (age lt 18 and role ne 'Admin')")
    translated_query = services.translate_query(query)
    compiled_query = translated_query.compile(
        engine, 
        compile_kwargs={"literal_binds": True})
    print(compiled_query)
    assert str(compiled_query) == expected_query

@pytest.mark.parametrize("operation, expected_query", [
    ("age not_existant 18",None),
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
def test_translate_operation(engine, operation, expected_query):
    services = QueryServices()
    
    if expected_query is None:
        with pytest.raises(InvalidOperatorException):
            services.translate_operation(operation)
        return

    parsed_operation = services.translate_operation(operation)
    compiled_query = parsed_operation \
        .compile(engine, compile_kwargs={"literal_binds": True})
    
    assert str(compiled_query) == expected_query

@pytest.mark.parametrize("query, expected_members", [
    (
        "age ge 18 and role eq 'Admin'",
        [["age ge 18", "role eq 'Admin'"]]
    ),
    (
        "age ge 18 and role eq 'Admin' or name eq 'John' and surname eq 'Doe'",
        [["age ge 18", "role eq 'Admin'"],["name eq 'John'","surname eq 'Doe'"]]
    ),
    (
        "name eq middlename or YEAR{birthdate} ge 1996",
        [["name eq middlename"],["YEAR{birthdate} ge 1996"]]
    )
])
def test_get_members(query, expected_members):
     services = QueryServices()
     members = services.get_members(query)
     print(members)
     
     assert members == expected_members

@pytest.mark.parametrize("query, expected_groups", [
    (
        "(age ge 18 or role eq 'Admin') and (age lt 18 or role ne 'Admin')",
        {
            0:"age ge 18 or role eq 'Admin'",
            1:"age lt 18 or role ne 'Admin'",
            2:"{0} and {1}"
        }
    ),
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
    ),
    (
        "(EXTRACT('year', birthdate) > 1996 and surname eq 'Doe') or (EXTRACT('year', driving_license_date) - EXTRACT('year', birthdate) > 5 and surname lk '%bar')",
        {
            0:"EXTRACT{'year', birthdate} > 1996 and surname eq 'Doe'",
            1:"EXTRACT{'year', driving_license_date} - EXTRACT{'year', birthdate} > 5 and surname lk '%bar'",
            2:"{0} or {1}"
        }
    ),
    (
        "(EXTRACT('year', birthdate) > 1996 and surname eq 'Doe') or (SUBTRACT(EXTRACT('year', driving_license_date), EXTRACT('year', birthdate)) > 5 and surname lk '%bar')",
        {
            0:"EXTRACT{'year', birthdate} > 1996 and surname eq 'Doe'",
            1:"SUBTRACT{EXTRACT{'year', driving_license_date}, EXTRACT{'year', birthdate}} > 5 and surname lk '%bar'",
            2:"{0} or {1}"
        }
    ),
    (
        "name eq middlename or EXTRACT('year', birthdate) ge 1996",
        {
            0:"name eq middlename or EXTRACT{'year', birthdate} ge 1996"
        }
    )
])
def test_get_groups(query, expected_groups):
    services = QueryServices()
    groups = services.get_groups(query)

    print(groups)
    
    assert groups == expected_groups
