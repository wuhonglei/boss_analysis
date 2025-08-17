from jinja2 import Template
from util.fs import read_json

from local_type import JobDetailItem, UserInput

single_job_template = Template("""\
岗位名称: {{ jobInfo.jobName }}
薪资范围: {{ jobInfo.salaryDesc }}
{% if jobInfo.degreeName %}学历要求: {{ jobInfo.degreeName }}{% endif %}
{% if jobInfo.experienceName %}经验要求: {{ jobInfo.experienceName }}{% endif %}
{% if jobInfo.showSkills %}技能要求: {{ jobInfo.showSkills | join(', ') }}{% endif %}
{{ jobInfo.postDescription }}
""")

prompt_template = Template("""
我是一名面试者，请根据我的职位搜索关键词和岗位描述，帮我分析当前招聘市场情况，并给出招聘建议。
职位搜索关键词: {{ search_keywords | join(', ') }}
学历: {{ user_input.degree }}
薪资: {{ user_input.salary }}
经验: {{ user_input.experience }}

详细岗位列表描述如下:
{{ job_description }}
""")


def get_single_job_str(job_detail: JobDetailItem) -> str:
    return single_job_template.render(job_detail)


def get_multi_job_str(job_details: list[JobDetailItem]) -> str:
    job_str_list = []
    for index, job in enumerate(job_details, 1):
        job_str = single_job_template.render(job)
        new_job_str = f'<岗位{index}>\n{job_str}\n</岗位{index}>'
        job_str_list.append(new_job_str)
    return '\n\n'.join(job_str_list)


def get_prompt(job_details: list[JobDetailItem], search_keywords: list[str], user_input: UserInput) -> str:
    job_description = get_multi_job_str(job_details)
    return prompt_template.render(search_keywords=search_keywords, job_description=job_description, user_input=user_input)


if __name__ == "__main__":
    job_detail = read_json('./data/jobdetail.json')
    # print(get_single_job_str(job_detail[0]))
    print(get_multi_job_str(job_detail[0:2]))
