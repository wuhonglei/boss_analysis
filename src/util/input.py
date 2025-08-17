import questionary

from config import degree_map, salary_map
from local_type import UserInput
from util.fs import read_json, write_json


def collect_user_input(exist_job_details: bool):
    last_user_input: UserInput = read_json(
        'data/user_input.json', {})  # type:ignore

    # 学历
    degree = questionary.select(
        "你的最高学历?",
        default=last_user_input.get('degree'),
        choices=list(degree_map.keys())[:3],
    ).ask()

    # 薪资
    salary = questionary.select(
        "你的期望薪资?",
        default=last_user_input.get(
            'salary') if last_user_input.get('salary') in salary_map else "其他",
        choices=salary_map + ['其他'],
    ).ask()

    if salary == '其他':
        salary = questionary.text(
            "请输入具体薪资范围（如：40-50K）:",
            default=last_user_input.get('salary', "40-50K")
        ).ask()

    # 工作经验
    experience = questionary.text(
        "你的工作经验(如：3年、5年、10年)?",
        default=last_user_input.get('experience', "3")
    ).ask()

    if exist_job_details:
        user_job_details = questionary.confirm(
            "是否使用已有的岗位信息? 如果使用, 则不需要重新搜索岗位",
            default=True
        ).ask()
    else:
        user_job_details = False

    current_user_input = UserInput(
        degree=degree, salary=salary, experience=experience, user_job_details=user_job_details)
    write_json(current_user_input, 'data/user_input.json')
    return current_user_input
