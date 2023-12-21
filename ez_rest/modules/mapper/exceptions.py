class InvalidFieldException(Exception):
    def __init__(self, invalid_field:str) -> None:
        super().__init__(f"Invalid field: {invalid_field}")

class MappingNotFoundException(Exception):
    def __init__(self, mapping_key) -> None:
        super().__init__(f"Mapping key not found: {mapping_key}")