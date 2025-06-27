from backend.query_expansion import expand_query
 
def test_expand_query_basic():
    result = expand_query("car")
    assert isinstance(result, list)
    assert "car" in result 