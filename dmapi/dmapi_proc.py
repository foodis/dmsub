import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from io import BytesIO
import pandas as pd
import base64
import json

def to_excel(r_data):
    try:
        data = json.loads(r_data)
        data_list = data.get("data", [])
        column_mapping = data.get("columns", {})

        df = pd.DataFrame(data_list)
        if column_mapping:
            df = df[list(column_mapping.keys())]  # 컬럼 순서 맞추기
            df = df.rename(columns=column_mapping)

        output = BytesIO()
        # ExcelWriter 한번만 사용
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)

        output.seek(0)
        excel_base64 = base64.b64encode(output.read()).decode("utf-8")
        return excel_base64
    except Exception as e:
        print(e)

def combine_answers(group):
    # item이 비어있으면 etcopinion(기타의견) 사용
    answers = group.apply(lambda r: r['item'] if str(r['item']).strip() != '' else '기타_' + str(r['etcopinion']),axis=1)
    return ", ".join(answers.unique())

def to_survey_data(r_data):
    try:
        data = json.loads(r_data)
        question_list = data.get("survey_question", [])
        respodent_list = data.get("survey_respodent_list", [])
        answer_list = data.get("survey_question_answer_list", [])

        df_question = pd.DataFrame(question_list)
        df_respondent = pd.DataFrame(respodent_list)
        df_answer = pd.DataFrame(answer_list)

        # 2. 답변 데이터에 질문 내용(question)을 결합 (questionid 기준)
        df_answer_with_q = pd.merge(
            df_answer,
            df_question[['questionid', 'question']],
            on='questionid',
            how='left'
        )

        df_pivot = (
            df_answer_with_q
            .groupby(['respondentid', 'questionid', 'question'], group_keys=False)
            .apply(combine_answers)
            .unstack(level=[1, 2])
        )

        # print(df_pivot.columns)
        # 1. MultiIndex의 첫 번째 레벨(questionid)을 기준으로 컬럼 오름차순 정렬
        df_pivot = df_pivot.sort_index(axis=1, level=0)

        qid_to_qno = {q['questionid']: q['questionno'] for q in question_list}

        # 컬럼명을 'Q1. 질문내용' 형태로 이쁘게 다듬기
        # df_pivot.columns = [f"Q{qid}_{qtxt}" for qid, qtxt in df_pivot.columns]
        # df_pivot.columns = [f"{qid_to_qno.get(qid, qid)}.{qtxt}" for qid, qtxt in df_pivot.columns]
        df_pivot.columns = [f"{qid_to_qno.get(qid, qid)}" for qid, qtxt in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        # 4. 최종적으로 응답자 정보 오른쪽에 질문별 답변 붙이기
        result_df = pd.merge(df_respondent, df_pivot, on='respondentid', how='left')
        result_df = result_df.fillna('')

        return result_df.to_dict('records')
    except Exception as e:
        raise e

def to_happycall_static_data(r_data):
    try:
        data = json.loads(r_data)
        sday = data.get("sday", '')
        eday = data.get("eday", '')
        happy_call_1 = data.get("happy_call_1", [])
        happy_call_2 = data.get("happy_call_2", [])
        survey_respondent_1 = data.get("survey_respondent_1", [])
        survey_respondent_2 = data.get("survey_respondent_2", [])

        date_list = pd.date_range(start=sday, end=eday, freq='D')
        m_data_list = [{'date_': str(ditem.strftime("%Y%m%d"))} for ditem in date_list]

        pd_m_data_list = pd.DataFrame(m_data_list)

        pd_happy_call_1 = pd.DataFrame(happy_call_1).rename(columns={'cnt_': 'cnt_h1'}) if happy_call_1 else pd.DataFrame(columns=['date_', 'cnt_h1'])
        pd_happy_call_2 = pd.DataFrame(happy_call_2).rename(columns={'cnt_': 'cnt_h2'}) if happy_call_2 else pd.DataFrame(columns=['date_', 'cnt_h2'])
        pd_survey_respondent_1 = pd.DataFrame(survey_respondent_1).rename(columns={'cnt_': 'cnt_r1'}) if survey_respondent_1 else pd.DataFrame(columns=['date_', 'cnt_r1'])
        pd_survey_respondent_2 = pd.DataFrame(survey_respondent_2).rename(columns={'cnt_': 'cnt_r2'}) if survey_respondent_2 else pd.DataFrame(columns=['date_', 'cnt_r2'])

        t_list = pd_m_data_list.merge(pd_happy_call_1, on='date_', how='left')\
                               .merge(pd_happy_call_2, on='date_', how='left') \
                               .merge(pd_survey_respondent_1, on='date_', how='left')\
                               .merge(pd_survey_respondent_2, on='date_', how='left')
        t_list = t_list.fillna(0)

        # 데이터가 비어있을 경우를 대비해 컬럼 보장 후 int 변환
        for col in ['cnt_h1', 'cnt_h2', 'cnt_r1', 'cnt_r2']:
            if col in t_list.columns:
                t_list[col] = t_list[col].astype('int')
            else:
                t_list[col] = 0

        t_list = t_list.sort_values(by=['date_'], ascending=False)
        sum_list = t_list[['cnt_h1', 'cnt_h2', 'cnt_r1', 'cnt_r2']].sum()

        return t_list.to_dict('records'), sum_list.to_dict()
    except Exception as e:
        raise e
