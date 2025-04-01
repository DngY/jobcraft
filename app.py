import gradio as gr
import PyPDF2
from docx import Document
import requests
import os

# 从文件中提取文本
def extract_text(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == ".pdf":
            # 处理 PDF 文件
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        elif file_ext == ".docx":
            # 处理 DOCX 文件
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        elif file_ext == ".doc":
            return "不支持 .doc 格式，请将文件转换为 .docx 或 .pdf 后再上传。"
        else:
            return "不支持的文件格式，仅支持 .docx 和 .pdf。"
    except Exception as e:
        return f"文本提取失败：{e}"

# 调用阿里通义千问 API
def call_tongyi_qwen_api(prompt):
    api_key = "YOUR_API_KEY"  # 请替换为您的实际 API 密钥
    endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-plus",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "parameters": {
            "max_tokens": 1500,
            "temperature": 0.7,
            "top_p": 0.8
        }
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()  # 检查响应状态
        result = response.json()
        
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"API 响应格式错误：{result}"
    except requests.exceptions.RequestException as e:
        return f"API 调用失败：{str(e)}"

# 生成求职应聘语
def generate_cover_letter(resume_file, job_description, word_limit):
    # 检查是否上传了简历文件
    if resume_file is None:
        return "请上传简历文件。"
    
    # 提取简历文本
    resume_text = extract_text(resume_file.name)  # Gradio 的 File 对象有 .name 属性
    if "文本提取失败" in resume_text or "不支持" in resume_text:
        return resume_text
    
    # 构造提示词
    prompt = (
        f"根据以下简历和岗位描述，生成一篇求职应聘语，突出候选人的相关技能和经验。"
        f"应聘语字数不得超过 {word_limit} 字。\n\n"
        f"简历：\n{resume_text}\n\n"
        f"岗位描述：\n{job_description}"
    )
    
    # 调用 API 生成文本
    generated_text = call_tongyi_qwen_api(prompt)
    if generated_text.startswith("API"):
        return generated_text
    
    # 检查并截断文本以满足字数限制
    if len(generated_text) > word_limit * 1.5:  # 假设平均每个汉字1.5个字符
        generated_text = generated_text[:int(word_limit * 1.5)] + "..."
    
    return generated_text

# 数据隐私声明
disclaimer = (
    "注意：使用此应用程序意味着您同意将简历和岗位描述发送至阿里通义千问 API 进行处理。"
    "请在使用前确认您对此感到满意。\n\n"
    "支持的文件格式：.docx, .pdf（不支持 .doc，请转换为支持的格式）。"
)

# 创建 Gradio 界面
iface = gr.Interface(
    fn=generate_cover_letter,
    inputs=[
        gr.File(label="上传简历 (支持 docx, pdf)"),
        gr.Textbox(label="岗位描述", lines=5, placeholder="请输入岗位招聘描述..."),
        gr.Number(label="字数限制", value=300, step=1)
    ],
    outputs=gr.Textbox(label="生成的求职应聘语", lines=10),
    title="AI 求职应聘语生成器",
    description=disclaimer
)

# 启动界面
iface.launch()
