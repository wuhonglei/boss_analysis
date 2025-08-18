import re

from local_type import JobDetailItem, JobListItem, UserInput
from config import degree_map, job_ignore_names, salary_map


def get_nested_value(obj: dict, key: str):
    """获取嵌套字典的值"""
    keys = key.split('.')
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def does_degree_match(degree_name: str, user_degree: str):
    if not degree_name:
        return True

    return degree_name in degree_map[user_degree]


def get_digit_from_str(s: str):
    return int(re.sub(r'\D', '', s))


def get_digit_by_pattern(s: str):
    pattern = r'\d+'
    match = re.match(pattern, s.strip())
    if match:
        return int(match.group())
    return 0


def does_salary_match(salary_desc_str: str, user_salary: str):
    if not salary_desc_str:
        return True

    black_words = ['天']
    for word in black_words:
        if word in salary_desc_str:
            return False

    salary_range = salary_desc_str.split('-')
    if len(salary_range) != 2:
        return True

    min_salary = get_digit_from_str(salary_range[0])
    max_salary = get_digit_by_pattern(salary_range[1])

    salary_range = [min_salary, max_salary]
    user_salary_range = [get_digit_from_str(x)
                         for x in user_salary.split('-')]

    return salary_range[0] <= user_salary_range[0] <= salary_range[1]


def does_experience_match(experience_name: str, user_experience: str):
    if not experience_name:
        return True

    experience_range = experience_name.split('-')
    if len(experience_range) != 2:
        return False

    min_experience = get_digit_from_str(experience_range[0])
    max_experience = get_digit_from_str(experience_range[1])

    min_user_experience = get_digit_from_str(user_experience.split('-')[0])

    return min_experience <= min_user_experience <= max_experience


def does_job_name_match(job_name: str, ignore_words: list[str]):
    if not job_name:
        return True

    for word in ignore_words:
        if word in job_name:
            return False
    return True


def filter_job_list(job_list: list[JobListItem], user_input: UserInput):
    if not job_list:
        return []

    if not user_input:
        return job_list

    filtered_job_list = []
    degree, salary, experience = user_input['degree'], user_input['salary'], user_input['experience']
    for job in job_list:
        degree_name = job['jobDegree']
        salary_desc = job['salaryDesc']
        experience_name = job['jobExperience']
        job_name = job['jobName']

        if not does_degree_match(degree_name, degree):
            continue
        if not does_salary_match(salary_desc, salary):
            continue
        if not does_experience_match(experience_name, experience):
            continue
        if not does_job_name_match(job_name, job_ignore_names):
            continue

        filtered_job_list.append(job)

    return filtered_job_list


def filter_job_details(job_details: list[JobDetailItem], user_input: UserInput):
    if not job_details:
        return []

    if not user_input:
        return job_details

    filtered_job_details = []
    degree, salary, experience = user_input['degree'], user_input['salary'], user_input['experience']
    for job_detail in job_details:
        job_info = job_detail['jobInfo']
        degree_name = job_info['degreeName']
        salary_desc = job_info['salaryDesc']
        experience_name = job_info['experienceName']
        job_name = job_info['jobName']

        if not does_degree_match(degree_name, degree):
            continue
        if not does_salary_match(salary_desc, salary):
            continue
        if not does_experience_match(experience_name, experience):
            continue
        if not does_job_name_match(job_name, job_ignore_names):
            continue

        filtered_job_details.append(job_detail)

    return filtered_job_details
