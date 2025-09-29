import flask
import os
from flask import Flask, request, jsonify, render_template
import requests, time, re
import datetime

app = Flask(__name__, static_folder="static", template_folder="static")

# 用于存储IP访问次数的字典
# 格式: { 'ip_address': {'count': number, 'last_reset': timestamp} }
ip_access_count = {}
# 每天最大访问次数
MAX_DAILY_ACCESS = 7


def limit_ip_access(func):
    """装饰器：限制同一IP每天的访问次数"""
    def wrapper(*args, **kwargs):
        # 获取客户端IP地址
        ip = request.remote_addr
        current_time = datetime.datetime.now()
        
        # 检查IP是否存在于记录中
        if ip in ip_access_count:
            access_info = ip_access_count[ip]
            last_reset = datetime.datetime.fromtimestamp(access_info['last_reset'])
            
            # 检查是否需要重置计数（过了一天）
            if (current_time - last_reset).days >= 1:
                # 重置访问计数
                ip_access_count[ip] = {
                    'count': 1,
                    'last_reset': current_time.timestamp()
                }
            else:
                # 检查是否超过最大访问次数
                if access_info['count'] >= MAX_DAILY_ACCESS:
                    # 计算剩余重置时间（秒）
                    next_reset = last_reset + datetime.timedelta(days=1)
                    reset_in_seconds = (next_reset - current_time).total_seconds()
                    hours, remainder = divmod(int(reset_in_seconds), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    remaining = 0
                    return jsonify({
                        "code": 429,
                        "message": f"访问次数过多，今日剩余次数：{remaining}次，请{hours}小时{minutes}分钟{seconds}秒后再试"
                    })
                
                # 增加访问计数
                ip_access_count[ip]['count'] += 1
        else:
            # 首次访问，初始化计数
            ip_access_count[ip] = {
                'count': 1,
                'last_reset': current_time.timestamp()
            }
        
        # 执行原函数
        # 获取当前IP的剩余次数
        ip = request.remote_addr
        current_count = ip_access_count.get(ip, {}).get('count', 1)
        remaining = MAX_DAILY_ACCESS - current_count
        
        # 执行原函数并获取响应
        response = func(*args, **kwargs)
        
        # 如果是JSON响应，添加剩余次数信息
        if isinstance(response, flask.wrappers.Response) and response.content_type == 'application/json':
            # 解析JSON内容
            import json
            data = json.loads(response.get_data(as_text=True))
            # 响应中添加剩余次数
            # if data.get('code') == 200:
            if True:
                data['remaining_times'] = remaining
                data['message'] = f"{data['message']}，今日剩余次数：{remaining}次"
                # 重新创建响应
                response.data = json.dumps(data)
        
        return response
    
    # 保留原函数的元数据
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

# 从环境变量中读取配置，如未设置则使用默认值
QL_HOST = os.environ.get('QL_HOST', '')
CLIENT_ID = os.environ.get('CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')

_cached_token = None
_token_expire_time = 0

def get_ql_token():
    global _cached_token, _token_expire_time
    if _cached_token and time.time() < _token_expire_time - 60:
        return _cached_token
    url = f"{QL_HOST}/open/auth/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"
    res = requests.get(url, verify=False)
    data = res.json()
    if data.get("code") != 200:
        raise Exception(f"获取Token失败: {data}")
    token = data["data"]["token"]
    _cached_token = token
    _token_expire_time = data["data"]["expiration"]
    return token

@app.route("/")
def index():
    return render_template("jdupdate.html")

# @app.route("/jdupdate")
# def jdupdate_page():
#     return render_template("jdupdate.html")

@app.route("/api/envs", methods=["GET"])
def get_envs():
    try:
        token = get_ql_token()
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{QL_HOST}/open/envs?searchValue=", headers=headers, verify=False, timeout=10)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})

@app.route("/api/jdcookie/query", methods=["GET"])
@limit_ip_access
def query_jdcookie():
    """
    查询参数: ptpin - 要查询的 pt_pin 值
    """
    try:
        ptpin = request.args.get("ptpin")
        if not ptpin:
            return jsonify({"code": 400, "message": "ptpin 参数不能为空"})

        token = get_ql_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 获取所有 JD_COOKIE
        res = requests.get(f"{QL_HOST}/open/envs?searchValue=JD_COOKIE", headers=headers, verify=False, timeout=10)
        envs_data = res.json()
        if envs_data.get("code") is not 200:
            return jsonify({"code": 500, "message": "获取环境变量失败"})

        envs = envs_data.get("data", [])
        # 找到匹配 pt_pin 的 cookie
        target_env = None
        for env in envs:
            if f"pt_pin={ptpin}" in env["value"]:
                target_env = env
                break
        if not target_env:
            return jsonify({"code": 404, "message": "未找到对应 pt_pin 的 JD_COOKIE"})

        # 返回环境变量的所有状态信息
        env_info = {
            "id": target_env["id"],
            "name": target_env["name"],
            "value": target_env["value"],
            "remarks": target_env.get("remarks", ""),
            "status": target_env.get("status", 1),  # 0: 启用, 1: 禁用
            "updatedAt": target_env.get("updatedAt", "")
        }
        
        return jsonify({"code": 200, "message": "查询成功", "data": env_info})

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})

@app.route("/api/jdcookie/update", methods=["POST"])
@limit_ip_access
def update_jdcookie():
    """
    body: { "value": "完整 JD_COOKIE 值" }
    """
    try:
        data = request.json
        new_value = data.get("value")
        if not new_value:
            return jsonify({"code": 400, "message": "JD_COOKIE 值不能为空"})

        # 从 value 中提取 pt_pin
        match = re.search(r"pt_pin=([^;]+);?", new_value)
        if not match:
            return jsonify({"code": 400, "message": "JD_COOKIE 中未找到 pt_pin"})
        pt_pin = match.group(1)

        token = get_ql_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 获取所有 JD_COOKIE
        res = requests.get(f"{QL_HOST}/open/envs?searchValue=JD_COOKIE", headers=headers, verify=False, timeout=10)
        envs_data = res.json()
        if envs_data.get("code") is not 200:
            return jsonify({"code": 500, "message": "获取环境变量失败"})

        envs = envs_data.get("data", [])
        # 找到匹配 pt_pin 的 cookie
        target_env = None
        for env in envs:
            if f"pt_pin={pt_pin}" in env["value"]:
                target_env = env
                break
        if not target_env:
            return jsonify({"code": 404, "message": "未找到对应 pt_pin 的 JD_COOKIE"})

        env_id = target_env["id"]
        status = target_env.get("status", 1)  # 默认禁用

        if status == 0:
            return jsonify({"code": 200, "message": "环境变量已启用，无需更新"})

        # 更新 value
        payload = {
            "id": env_id,
            "name": target_env["name"],
            "value": new_value,
            "remarks": target_env.get("remarks", "")
        }
        res_update = requests.put(f"{QL_HOST}/open/envs", headers=headers, json=payload, verify=False, timeout=10)
        update_result = res_update.json()
        if update_result.get("code") is not 200:
            return jsonify({"code": 500, "message": f"更新环境变量失败: {update_result}"})

        # 启用环境变量
        enable_payload = [env_id]
        res_enable = requests.put(
            f"{QL_HOST}/open/envs/enable",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=enable_payload,
            verify=False,
            timeout=10
        )
        enable_result = res_enable.json()
        if enable_result.get("code") != 200:
            return jsonify({"code": 500, "message": f"启用环境变量失败: {enable_result}"})

        return jsonify({"code": 200, "message": "更新并启用成功"})

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
