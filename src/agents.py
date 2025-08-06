from crewai import Crew, Process, Agent, Task
import yaml


# Load YAML
def load_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

agent_config = load_yaml("src/configs/agents.yaml")
task_config = load_yaml("src/configs/tasks.yaml")


# Agents 

tutor = Agent(
    role=agent_config["tutor"]["role"],
    goal=agent_config["tutor"]["goal"],
    backstory=agent_config["tutor"]["backstory"],
    verbose=True,
    # memory=True,
    allow_delegation=False,

)

translator = Agent(
    role=agent_config["translator"]["role"],
    goal=agent_config["translator"]["goal"],
    backstory=agent_config["translator"]["backstory"],
    verbose=True,
    # memory=True,
    allow_delegation=False,
)


def task2(lang, context, additional_info):
    task2 = Task(
        description=task_config["translate"]["description"].format(language=lang, context=context, additional_info=additional_info),
        expected_output=task_config["translate"]["expected_output"],
        agent=translator,
    )
    return task2

def task1(lang, context, additional_info):
    task1 = Task(
        description=task_config["teach"]["description"].format(language=lang, context=context, additional_info=additional_info),
        expected_output=task_config["teach"]["expected_output"],
        agent=tutor,
    )
    return task1