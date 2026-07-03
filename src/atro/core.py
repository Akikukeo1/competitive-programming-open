from atro.contest.ahc import init_ahc
from atro.contest.abc import init_abc


def init_contest(contest_type, contest_name, objective, language, interactive, tools_url=None):
    if contest_type == "ahc":
        init_ahc(contest_name, objective, language, interactive, tools_url)
    elif contest_type == "abc":
        init_abc(contest_name, language)
