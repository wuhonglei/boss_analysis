from jinja2 import Template
from util.fs import read_json

from local_type import JobDetailItem, UserInput

single_job_template = Template("""\
岗位名称: {{ jobInfo.jobName }}
薪资范围: {{ jobInfo.salaryDesc }}
公司名称: {{ brandComInfo.brandName }}
工作地点: {{ jobInfo.address }}
行业名称: {{ brandComInfo.industryName }}
公司规模: {{ brandComInfo.scaleName }}
融资情况: {{ brandComInfo.stageName }}
{% if jobInfo.degreeName %}学历要求: {{ jobInfo.degreeName }}{% endif %}
{% if jobInfo.experienceName %}经验要求: {{ jobInfo.experienceName }}{% endif %}
{% if jobInfo.showSkills %}技能要求: {{ jobInfo.showSkills | join(', ') }}{% endif %}
{{ jobInfo.postDescription }}
""")

prompt_template = Template("""
我是一名面试者，请根据我的职位搜索关键词和岗位描述，帮我分析当前招聘市场情况，并给出面试建议。
职位搜索关键词: {{ user_input.job_names | join(', ') }}
学历: {{ user_input.degree }}
工作经验: {{ user_input.experience }}
期望薪资: {{ user_input.salary }}
{% if user_input.other_info %}其他补充信息: {{ user_input.other_info }}{% endif %}
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


def get_prompt(job_details: list[JobDetailItem], user_input: UserInput) -> str:
    job_description = get_multi_job_str(job_details)
    return prompt_template.render(job_description=job_description, user_input=user_input)


if __name__ == "__main__":
    job_details = read_json('./data/jobdetail.json', [])
    # print(get_single_job_str(job_detail[0]))
    print(get_multi_job_str(job_details[0:2]))
