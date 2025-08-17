import questionary

from config import degree_map, salary_map
from local_type import UserInput


def collect_user_input(exist_job_details: bool):
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

    if exist_job_details:
        user_job_details = questionary.confirm(
            "是否使用已有的岗位信息? 如果使用, 则不需要重新搜索岗位",
            default=True
        ).ask()
    else:
        user_job_details = False

    return UserInput(degree=degree, salary=salary, experience=experience, user_job_details=user_job_details)
