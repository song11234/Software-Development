"""配置管理 —— 通过环境变量加载，Pydantic 校验。

对应知识点：第02章 MCP/SaaS 配置管理、第07章 Harness 安全护栏中的 token budget。
"""
import os
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class AppConfig(BaseModel):
    """应用全局配置，所有字段带默认值和校验。"""
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI 兼容 API 密钥"
    )
    openai_base_url: str = Field(
        default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        description="API 基础 URL"
    )
    model_name: str = Field(
        default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"),
        description="模型名称"
    )
    api_token: str = Field(
        default_factory=lambda: os.getenv("COURSE_API_TOKEN", "dev-local-token"),
        description="API 认证令牌"
    )
    max_tokens_per_request: int = Field(
        default_factory=lambda: int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000")),
        ge=100, le=16000,
        description="单次请求 Token 预算上限"
    )
    rate_limit_per_minute: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "20")),
        ge=1,
        description="每分钟请求频率上限"
    )
    documents_dir: str = Field(
        default_factory=lambda: os.getenv("DOCUMENTS_DIR", "./data/documents"),
        description="文档存储目录"
    )
    host: str = Field(
        default_factory=lambda: os.getenv("HOST", "0.0.0.0"),
        description="服务监听地址"
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000")),
        ge=1024, le=65535,
        description="服务监听端口"
    )

    def is_api_key_valid(self) -> bool:
        """检查 API Key 是否有效。"""
        return bool(self.openai_api_key) and self.openai_api_key != "sk-your-key-here"


@lru_cache()
def get_config() -> AppConfig:
    """懒加载全局配置单例（带缓存）。

    不在导入时强制校验 API Key，允许在无 Key 环境下运行测试。
    调用 AI 功能前通过 config.is_api_key_valid() 检查。
    """
    return AppConfig()
