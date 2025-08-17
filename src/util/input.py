import questionary

from config import degree_map, salary_map
from local_type import UserInput


def collect_user_input():
    # 学历
    degree = questionary.select(
        "你的最高学历?",
        choices=list(degree_map.keys())[:3],
    ).ask()

    # 薪资
    salary = questionary.select(
        "你的期望薪资?",
        choices=salary_map + ['其他'],
    ).ask()

    if salary == '其他':
        salary = questionary.text(
            "请输入具体薪资范围（如：40-50K）:",
            default="40-50K"
        ).ask()

    # 工作经验
    experience = questionary.text(
        "你的工作经验(如：3年、5年、10年)?",
        default="3"
    ).ask()
    return UserInput(degree=degree, salary=salary, experience=experience)
