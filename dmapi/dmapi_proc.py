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
