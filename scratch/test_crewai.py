import inspect
from copilotkit.crewai import CrewAIAgent

print("CrewAIAgent.execute signature:")
print(inspect.signature(CrewAIAgent.execute))
print("\nCrewAIAgent.execute source code:")
print(inspect.getsource(CrewAIAgent.execute))
