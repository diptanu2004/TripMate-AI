from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

# res = tavily_search.invoke({"query": "What are the best tourist attractions in Paris?"})

# print(res)
res = search_flights.invoke({"origin": "DAC", "destination": "DEL", "limit": 5})

print("Flight Search Results:\n")
print(res)