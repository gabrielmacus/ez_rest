class QueryServices:
    
    def split_filter_members(self, query:str):
        members = [m.replace("").strip() for m in query.split('and')]
        return members
    