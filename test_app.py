from ai_pipeline import is_weather_query, answer_query

def test_is_weather_query():
    assert is_weather_query("What's the weather in Pune?")
    assert not is_weather_query("Tell me about quantum computing.")

def test_answer_query_weather(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "dummy")
    
    assert "Please specify a city" in answer_query("What is the weather?")