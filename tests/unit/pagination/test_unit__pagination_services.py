from ez_rest.modules.pagination.services import PaginationServices
import pytest
import os


TEST_DB_PATH = 'test.db'
TEST_DB_URI = f'sqlite:///{TEST_DB_PATH}'

os.environ['DB_CONNECTION_STRING'] = TEST_DB_URI


@pytest.mark.parametrize("page,limit,expected_offset", 
                         [(1,20,0),
                          (2,20,20),
                          (3,30,60)])
def test_get_offset(page, limit, expected_offset):
    services = PaginationServices()
    assert expected_offset == services.get_offset(page, limit)

@pytest.mark.parametrize("count, limit, expected_pages", 
                         [(1000, 20, 50),
                          (934,30,32),
                          (123431,30,4115)])
def test_get_pages_count(count, limit, expected_pages):
    services = PaginationServices()
    assert services.get_pages_count(count, limit) == expected_pages
