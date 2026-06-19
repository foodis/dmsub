import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import json
import traceback
import dmapi_proc as dmpr

def main():
    try:
        r_data = sys.stdin.read()
        if not r_data.strip():
            raise ValueError("No input received")

        r_list, s_list = dmpr.to_happycall_static_data(r_data)
        response_dict = {
            "status": "success",
            "file_data": r_list,
            "file_data2": s_list
        }

        # JSON만 출력
        sys.stdout.write(json.dumps(response_dict))
        sys.stdout.flush()
        sys.exit(0)

    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

        # JSON만 출력 (print(e) 제거)
        sys.stdout.write(json.dumps(error_response))
        sys.stdout.flush()
        sys.exit(1)
if __name__ == "__main__":
    main()
