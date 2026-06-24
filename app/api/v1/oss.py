import os
from datetime import timedelta

import alibabacloud_oss_v2 as oss
from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv()
router = APIRouter()

# 从环境变量中加载阿里云凭证（AK/SK）
credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()

cfg = oss.config.load_default()
cfg.credentials_provider = credentials_provider

# 仅指定 Region，SDK 会自动构造 HTTPS 域名
cfg.region = "cn-beijing"

client = oss.Client(cfg)

OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
OSS_BUCKET = os.getenv("OSS_BUCKET")


@router.get("/oss/presign")
def oss_presign(filename: str):
    """生成上传图片用的预签名 URL"""
    content_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = content_type_map.get(ext, "application/octet-stream")

    pre_result = client.presign(
        oss.PutObjectRequest(
            bucket=OSS_BUCKET,
            key=filename,
            content_type=content_type,
        ),
        expires=timedelta(seconds=3600),
    )

    return {
        "uploadUrl": pre_result.url.strip('"'),
        "contentType": content_type,
        "accessUrl": f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{filename}",
    }
