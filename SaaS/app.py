# ==================== 依赖导入 ====================
# gradio 负责构建本地 Web UI；json/csv/tempfile 负责工具之间的数据交换和文件导出；
# logging 用于记录 Agent 每一轮决策，OpenAI SDK 用于调用 DeepSeek 的兼容接口。
import gradio as gr
import json
import os
import time
import csv
import tempfile
import logging
from datetime import datetime
from openai import OpenAI

# ==================== 日志配置 ====================
# 日志同时写入文件和终端：
# - 文件日志便于课后复盘 Agent 的工具调用链；
# - 终端日志便于课堂实时观察模型是否按预期规划。
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 初始化客户端 ====================
# 本课程使用 DeepSeek 云端 API，OpenAI SDK 可直接调用其兼容接口。
# timeout=120 用于给网络请求和首轮推理留出足够时间。
# api_key 优先从环境变量 DEEPSEEK_API_KEY 读取；未设置时客户端保持为 None，仅用于业务逻辑测试。
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

if DEEPSEEK_API_KEY:
    try:
        client = OpenAI(
            base_url='https://api.deepseek.com/v1',
            api_key=sk-3dac5773b1d944a687797df26aaaaa87
,
            timeout=120
        )
        print("DeepSeek 客户端初始化成功")
    except Exception as e:
        print(f"DeepSeek 客户端初始化失败: {e}")
        raise
else:
    print("未检测到有效的 DEEPSEEK_API_KEY，仅测试业务逻辑")
    client = None

# ==================== 模拟底层数据 ====================
# 为了让实验可离线、可复现，这里不用真实数据库，而是用内存列表模拟员工花名册。
# 每条员工记录只保留 Agent 工具链所需的最小字段：id、name、level。
mock_employees = [
    {"id": "E01", "name": "张三", "level": "L1"},
    {"id": "E02", "name": "李四", "level": "L2"},
    {"id": "E03", "name": "王五", "level": "L3"}
]

# 职级到基础工资的映射表，后续工资计算工具会根据 level 查表。
mock_salary_levels = {"L1": 10000, "L2": 20000, "L3": 35000}

# 工具 A：仅负责查询全量员工基础数据
def get_employee_directory():
    """返回全公司员工的花名册 JSON。

    该函数模拟企业 HR 系统中的“员工目录服务”。
    Agent 调用它不需要任何参数，因此它通常是工具链第一步。
    """
    try:
        # 即使模拟数据为空，也返回 JSON 错误对象，避免上层拿到 None。
        if not mock_employees:
            return json.dumps({"error": "员工数据为空"}, ensure_ascii=False)

        # ensure_ascii=False 可以保留中文姓名，方便前端和日志直接阅读。
        return json.dumps(mock_employees, ensure_ascii=False)
    except Exception as e:
        # 工具函数统一返回 JSON 字符串，让模型可以把错误当作上下文继续处理。
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)

# 工具 B：仅负责算薪与扣税 (不关心数据从哪来，只负责处理传入的 JSON)
def calculate_payroll_and_tax(employees_json: str):
    """接收员工 JSON，计算五险一金、个税和实发工资。"""
    try:
        # 模型生成的参数不可信，先检查空值，避免 json.loads 抛出难懂错误。
        if not employees_json or not employees_json.strip():
            return json.dumps({"error": "输入数据为空"}, ensure_ascii=False)
        
        try:
            # 将上一个工具返回的 JSON 字符串恢复为 Python 列表。
            employees = json.loads(employees_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"JSON 解析失败: {str(e)}"}, ensure_ascii=False)
        
        # 本工具只接受员工数组；如果模型传入对象或普通文本，应明确拒绝。
        if not isinstance(employees, list):
            return json.dumps({"error": "输入数据格式错误，应为数组"}, ensure_ascii=False)
        
        if len(employees) == 0:
            return json.dumps({"error": "员工列表为空"}, ensure_ascii=False)
        
        results = []
        for emp in employees:
            # 容错：列表中如果混入非字典数据，跳过该项，避免整批失败。
            if not isinstance(emp, dict):
                continue

            # level 是计算工资的关键字段，缺失时保留该员工记录并追加错误说明。
            if "level" not in emp:
                emp_result = emp.copy()
                emp_result["error"] = "缺少 level 字段"
                results.append(emp_result)
                continue
            
            # 根据职级查基础工资。未知职级返回 0，并被视为业务错误。
            base_salary = mock_salary_levels.get(emp["level"], 0)
            if base_salary <= 0:
                emp_result = emp.copy()
                emp_result["error"] = f"无效的职级: {emp.get('level')}"
                results.append(emp_result)
                continue
            
            # 简化版薪酬规则：
            # - 五险一金按基础工资 20% 计算；
            # - 个税按扣除五险一金后的 5% 计算；
            # - 实发工资 = 基础工资 - 五险一金 - 个税。
            social_security = base_salary * 0.20
            tax = max(0, (base_salary - social_security) * 0.05)
            net_salary = base_salary - social_security - tax
            
            # 在原始员工信息上追加工资字段，方便导出和前端展示。
            emp_result = emp.copy()
            emp_result.update({
                "应发工资": base_salary,
                "五险一金扣除": social_security,
                "个税扣除": tax,
                "实发工资": net_salary
            })
            results.append(emp_result)
        
        if not results:
            return json.dumps({"error": "没有有效的员工数据"}, ensure_ascii=False)
            
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        # 所有未预期异常也转为 JSON，保持工具协议稳定。
        return json.dumps({"error": f"计算失败: {str(e)}"}, ensure_ascii=False)

# 工具 C：仅负责将传入的 JSON 写成物理 CSV 文件
def export_payroll_csv(payroll_json: str):
    """接收算好工资的 JSON，生成 CSV 文件并返回系统路径。"""
    try:
        # CSV 导出工具同样要先检查模型传入的参数是否为空。
        if not payroll_json or not payroll_json.strip():
            return json.dumps({"error": "输入数据为空"}, ensure_ascii=False)
        
        try:
            # 将工资 JSON 转成 Python 列表，供 csv.DictWriter 写入。
            payroll_data = json.loads(payroll_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"JSON 解析失败: {str(e)}"}, ensure_ascii=False)
        
        # 至少需要一条记录才能确定 CSV 表头。
        if not isinstance(payroll_data, list) or len(payroll_data) == 0:
            return json.dumps({"error": "工资数据为空或格式错误"}, ensure_ascii=False)
        
        # 使用系统临时目录，避免同学需要提前创建输出文件夹。
        filepath = os.path.join(tempfile.gettempdir(), "payroll_report.csv")
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                # 以第一条工资记录的字段作为表头，要求上游工具保持字段一致。
                writer = csv.DictWriter(f, fieldnames=payroll_data[0].keys())
                writer.writeheader()
                writer.writerows(payroll_data)
        except IOError as e:
            return json.dumps({"error": f"文件写入失败: {str(e)}"}, ensure_ascii=False)
            
        return json.dumps({"status": "success", "file_path": filepath, "record_count": len(payroll_data)}, ensure_ascii=False)
    except Exception as e:
        # 文件权限、磁盘空间等异常也以 JSON 形式返回给 Agent。
        return json.dumps({"error": f"导出失败: {str(e)}"}, ensure_ascii=False)

def saas_generate_payroll_api():
    """传统 SaaS 后端接口：硬编码的流水线，高度耦合。

    传统 SaaS 的特点是“程序员先规定流程，用户只能按流程操作”。
    本函数把查询、计算、导出三个步骤固定串在一起，作为 Agent 方案的对照组。
    """
    try:
        # 模拟系统耗时，方便同学在前端观察按钮触发后的处理过程。
        time.sleep(1)
        
        # 步骤 1：查询员工目录。这里用 error 字段做简化错误判断。
        emp_str = get_employee_directory()
        if "error" in emp_str:
            raise Exception(emp_str)

        # 步骤 2：工资计算。控制器必须显式知道第二步调用哪个函数。
        payroll_str = calculate_payroll_and_tax(emp_str)
        if "error" in payroll_str:
            raise Exception(payroll_str)

        # 步骤 3：导出 CSV。即使用户只想看结果，传统流程也会按代码固定执行。
        export_result = json.loads(export_payroll_csv(payroll_str))
        if "error" in export_result:
            raise Exception(export_result["error"])
        
        # Gradio Dataframe 需要二维数组，因此要把 JSON 对象转成表格行。
        payroll_data = json.loads(payroll_str)
        table_data = [[d["name"], d["level"], d["应发工资"], d["五险一金扣除"], d["实发工资"]] for d in payroll_data]
        
        # 严格返回两个输出：第一个给表格，第二个给文件下载组件。
        return table_data, export_result.get("file_path")
    except Exception as e:
        # 失败时也返回 Dataframe 可显示的二维数组，避免前端组件类型不匹配。
        print(f"❌ SaaS 执行失败: {e}")
        return [[str(e), "", "", "", ""]], None

# MCP 风格的工具说明书：告诉大模型“有哪些工具、什么时候用、参数怎么填”。
# 需要注意：模型只看到 Schema，不会直接看到或执行 Python 函数体。
tools_schema = [
    {
        # 每个工具都以 function 形式暴露给模型。
        "type": "function",
        "function": {
            # name 必须和后续 Python 路由中的函数名完全一致。
            "name": "get_employee_directory",
            # description 会直接影响模型是否选择这个工具，应写清楚调用时机。
            "description": "第一步：获取全公司所有员工的基础数据（包含姓名和职级）。不需要参数。"
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_payroll_and_tax",
            "description": "第二步：接收员工基础数据 JSON，计算实发工资。必须在获取员工名单后调用。",
            "parameters": {
                # JSON Schema 的 object 表示该工具需要接收命名参数。
                "type": "object",
                "properties": {
                    # employees_json 的描述告诉模型：这个参数应来自上一个工具的输出。
                    "employees_json": {"type": "string", "description": "由 get_employee_directory 返回的 JSON 数据"}
                },
                # required 可以减少模型漏填关键参数的概率。
                "required": ["employees_json"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_payroll_csv",
            "description": "第三步：将工资详细信息的 JSON 数据导出为 CSV 文件。必须在计算完工资后调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    # payroll_json 必须接收已经计算后的工资明细，而不是原始员工目录。
                    "payroll_json": {"type": "string", "description": "由 calculate_payroll_and_tax 返回的工资 JSON"}
                },
                "required": ["payroll_json"]
            }
        }
    }
]

def agent_orchestrator(user_message, history, messages_state, selected_model):
    """
    Agent 的大脑调度器。接收用户指令，并根据选择的模型（deepseek-chat 或 deepseek-reasoner）进行推理。

    history 是 Gradio Chatbot 可见历史；messages_state 是真正发给模型的上下文。
    二者分开保存，是为了让前端展示更友好，同时保留 tool 消息给模型继续推理。
    """
    # Gradio 首次调用时可能传入 None，这里统一转为空列表，避免后续 append 报错。
    history = history or []
    messages_state = messages_state or []

    try:
        logger.info(f"开始处理用户请求: {user_message}, 模型: {selected_model}")
        
        # 1. 严格的 System Prompt，框定 Agent 行为规范。
        # 只在新会话第一次初始化，避免每轮重复追加 system 消息。
        if not messages_state:
            messages_state = [{"role": "system", "content": "你是专业的 HR 助手。请自动规划工具调用链完成计算。输出最终结果时，请用 Markdown 表格展示，并附上文件下载路径。"}]
            logger.info("初始化系统提示词")
        
        # 将用户自然语言写入模型上下文；同时构造前端可见的“正在规划”提示。
        messages_state.append({"role": "user", "content": user_message})
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": f"🤖 [当前引擎: {selected_model}] 正在规划任务流..."}
        ]
        yield history, messages_state
        
        # 2. 开启多轮循环：这是实现多工具接力 (Chain of Actions) 的核心机制。
        # max_iterations 是安全阀，避免模型不断调用工具导致无限循环。
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"开始迭代 {iteration}/{max_iterations}")
            
            try:
                # 向所选模型发起请求，赋予其 tool_choice="auto" 的自主权。
                # 模型可以选择直接回答，也可以选择调用 tools_schema 中声明的工具。
                logger.info(f"调用模型 {selected_model} 进行推理")
                response = client.chat.completions.create(
                    model=selected_model, 
                    messages=messages_state, 
                    tools=tools_schema, 
                    tool_choice="auto"
                )
                response_msg = response.choices[0].message
                tool_calls = response_msg.tool_calls or []

                # OpenAI SDK 返回的是消息对象；为了让下一轮请求、Gradio State 和测试都稳定，
                # 这里显式转换成 OpenAI Chat Completions 接口可接受的 dict。
                assistant_message = {"role": "assistant", "content": response_msg.content}
                if tool_calls:
                    assistant_message["tool_calls"] = []
                    for index, tool_call in enumerate(tool_calls, start=1):
                        raw_tool_call_id = getattr(tool_call, "id", None)
                        tool_call_id = raw_tool_call_id if isinstance(raw_tool_call_id, str) else f"tool_call_{iteration}_{index}"
                        raw_tool_call_type = getattr(tool_call, "type", "function")
                        tool_call_type = raw_tool_call_type if isinstance(raw_tool_call_type, str) else "function"
                        assistant_message["tool_calls"].append({
                            "id": tool_call_id,
                            "type": tool_call_type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments or "{}"
                            }
                        })
                messages_state.append(assistant_message)
                
                # 3. 拦截判断：模型是否要求调用底层工具？
                # 如果出现 tool_calls，说明模型还需要程序执行真实业务函数。
                if tool_calls:
                    logger.info(f"模型请求调用 {len(tool_calls)} 个工具")
                    
                    for index, tool_call in enumerate(tool_calls, start=1):
                        func_name = tool_call.function.name
                        logger.info(f"准备调用工具: {func_name}")
                        
                        # 解析模型推理出的参数。
                        # tool_call.function.arguments 是 JSON 字符串，不是 Python 字典。
                        try:
                            func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                            logger.info(f"工具参数: {func_args}")
                        except json.JSONDecodeError as e:
                            # 参数解析失败时使用空参数进入工具逻辑，让工具返回结构化错误。
                            logger.warning(f"工具参数解析失败: {e}")
                            func_args = {}
                        
                        # 在前端流式打印当前的执行进度
                        history[-1]["content"] += f"\n\n> 🛠️ **触发节点**: `{func_name}`"
                        yield history, messages_state
                        
                        # 4. 动态路由：实际执行本地 Python 业务代码。
                        # 模型只负责“选择工具和填写参数”，真正的权限边界仍由工程代码控制。
                        start_time = time.time()
                        if func_name == "get_employee_directory":
                            tool_result = get_employee_directory()
                        elif func_name == "calculate_payroll_and_tax":
                            tool_result = calculate_payroll_and_tax(employees_json=func_args.get("employees_json", "[]"))
                        elif func_name == "export_payroll_csv":
                            tool_result = export_payroll_csv(payroll_json=func_args.get("payroll_json", "[]"))
                        else:
                            logger.error(f"未找到指定工具: {func_name}")
                            tool_result = json.dumps({"error": f"未找到指定工具: {func_name}"})
                        
                        execution_time = time.time() - start_time
                        logger.info(f"工具 {func_name} 执行完成，耗时: {execution_time:.2f}秒")
                        
                        # 5. 上下文回注：将物理世界的真实执行结果，作为 Context 塞回给大模型。
                        # role=tool 和 tool_call_id 必须保留，否则模型无法知道该结果对应哪个工具调用。
                        raw_tool_call_id = getattr(tool_call, "id", None)
                        tool_call_id = raw_tool_call_id if isinstance(raw_tool_call_id, str) else f"tool_call_{iteration}_{index}"
                        messages_state.append({
                            "role": "tool", "tool_call_id": tool_call_id, "name": func_name, "content": tool_result
                        })
                        logger.info(f"工具结果已回注到上下文")
                    
                    # 【重点】遇到 continue 意味着当前循环不退出。
                    # 模型会带着刚才的工具结果进入下一轮判断，决定是否继续调用下一个工具。
                    logger.info("继续下一轮迭代")
                    continue 

                else:
                    # 6. 出口条件：当大模型认为所有工具调用完毕，它会输出自然语言总结，此时退出循环。
                    final_text = response_msg.content or "任务已完成，但模型没有返回文本结果。"
                    logger.info(f"模型输出最终结果: {final_text[:100]}...")
                    
                    history[-1] = {"role": "assistant", "content": final_text}
                    yield history, messages_state
                    break 
                    
            except Exception as e:
                # 单轮推理失败时不清空上下文，保留日志和前端状态用于课堂排错。
                logger.error(f"迭代 {iteration} 执行失败: {str(e)}", exc_info=True)
                error_msg = f"❌ 迭代 {iteration} 执行失败: {str(e)}"
                history[-1]["content"] += f"\n\n{error_msg}"
                yield history, messages_state
                break
                
        if iteration >= max_iterations:
            # 达到轮次上限通常意味着模型没有形成终止判断，是 Agent 系统常见风险。
            logger.warning(f"已达到最大迭代次数 {max_iterations}，任务可能未完成")
            history[-1]["content"] += "\n\n⚠️ 已达到最大迭代次数，任务可能未完成"
            yield history, messages_state
            
        logger.info(f"用户请求处理完成，总迭代次数: {iteration}")
            
    except Exception as e:
        # 外层兜底覆盖初始化、参数类型、前端状态等非单轮模型调用错误。
        logger.error(f"Agent 调度器执行失败: {str(e)}", exc_info=True)
        error_msg = f"❌ Agent 调度器执行失败: {str(e)}"
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": error_msg}
        ]
        yield history, messages_state

# 使用 Gradio 构建现代且极简的 Web UI
with gr.Blocks() as demo:
    # 页面标题说明本实验的双轨对比主题。
    gr.Markdown("## 💸 现代软件架构实验：SaaS 巨石架构 vs Agent 动态编排")
    
    with gr.Row():
        # ================= 控制组：传统 SaaS 面板 =================
        with gr.Column(scale=1):
            # 左侧展示传统“按钮触发固定后端流程”的产品形态。
            gr.Markdown("### 🏢 控制组：SaaS (硬编码)")
            gr.Markdown("> 极度高效，但极度死板。开发者提前锁死了业务流。")
            
            # 三个输出组件分别承接：触发按钮、工资表格、导出的 CSV 文件。
            saas_btn = gr.Button("🚀 一键执行：生成工资单并下载", variant="primary")
            saas_table = gr.Dataframe(headers=["姓名", "职级", "应发", "五险一金", "实发"])
            saas_file = gr.File(label="导出的物理文件")
            
            # 事件绑定：点击按钮即触发巨石函数
            saas_btn.click(fn=saas_generate_payroll_api, inputs=None, outputs=[saas_table, saas_file])
            
        # ================= 实验组：AI Agent 面板 =================
        with gr.Column(scale=1):
            # 右侧展示自然语言驱动的 Agent 编排过程。
            gr.Markdown("### 🤖 实验组：Agent (意图驱动)")
            
            # 【实验核心变量控制】允许动态切换 DeepSeek 模型进行观察
            model_selector = gr.Dropdown(
                choices=["deepseek-chat", "deepseek-reasoner"],
                value="deepseek-chat",
                label="🧪 核心变量：选择 DeepSeek 模型"
            )
            
            # messages_state 保存发给模型的完整上下文；chatbot 只负责前端可见展示。
            messages_state = gr.State([]) 
            chatbot = gr.Chatbot(label="Agent 神经推理中枢日志", height=450)
            chat_input = gr.Textbox(label="自然语言指令", placeholder="输入测试用例：帮我查一下全公司的工资，算好扣税，然后给我个 CSV 文件")
            
            # 事件绑定：将用户输入和选择的模型参数一并传入智能调度器
            chat_input.submit(
                fn=agent_orchestrator, 
                inputs=[chat_input, chatbot, messages_state, model_selector], 
                outputs=[chatbot, messages_state]
            ).then(lambda: "", None, chat_input)

if __name__ == "__main__":
    # Gradio 6 将 theme 参数放在 launch 阶段设置，这样运行时不会出现迁移警告。
    demo.launch(theme="soft")