import questionary

from config import degree_map, salary_map
from local_type import UserInput
from util.fs import read_json, write_json


def collect_user_input(exist_job_details: bool):
    last_user_input: UserInput = read_json(
        'data/user_input.json', {})  # type:ignore

    # 岗位名称
    job_name = questionary.text(
        "你想要搜索的岗位名称(多个岗位用逗号分隔)",
        default=','.join(last_user_input.get('job_names', [])),
        validate=lambda x: len(x.strip()) > 0,
    ).ask()

    # 学历
    degree = questionary.select(
        "你的最高学历?",
        default=last_user_input.get('degree'),
        choices=list(degree_map.keys())[:3],
    ).ask()

    # 薪资
    salary = questionary.select(
        "你的期望薪资",
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
        "你的工作经验(如：3年、5年、10年)",
        default=last_user_input.get('experience', "3")
    ).ask()

    other_info = questionary.text(
        "请输入其他补充信息(如：当前职位)",
        default=last_user_input.get('other_info', ""),
    ).ask()

    if exist_job_details:
        user_job_details = questionary.confirm(
            "是否使用已有的岗位信息? 如果使用, 则不需要重新搜索岗位",
            default=True
        ).ask()
    else:
        user_job_details = False

    max_size = questionary.text(
        "想要检索的最大岗位数量(如：30):",
        default=str(last_user_input.get('max_size', 30))
    ).ask()

    current_user_input = UserInput(
        degree=degree,
        salary=salary,
        experience=experience,
        user_job_details=user_job_details,
        other_info=other_info,
        max_size=int(max_size),
        job_names=[name.strip()
                   for name in job_name.split(',') if name.strip()],
    )
    write_json(current_user_input, 'data/user_input.json')
    return current_user_input
