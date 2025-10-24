"""
生鲜环比数据处理API接口
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
import shutil
import tempfile

from app.processors.fresh_food_ratio import process_fresh_food_ratio

logger = logging.getLogger(__name__)
router = APIRouter()

# 临时文件存储目录
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


@router.post("/process-fresh-food-ratio")
async def process_fresh_food_ratio_api(
    last_month_file: UploadFile = File(..., description="上个月订单数据Excel文件"),
    this_month_file: UploadFile = File(..., description="本月订单数据Excel文件"),
    output_filename: Optional[str] = Form(None, description="输出文件名（可选）")
) -> Dict[str, Any]:
    """
    处理生鲜环比数据

    Args:
        last_month_file: 上个月订单数据的Excel文件
        this_month_file: 本月订单数据的Excel文件
        output_filename: 输出文件名（可选）

    Returns:
        处理结果，包含下载链接和统计信息
    """
    try:
        logger.info("开始处理生鲜环比数据API请求...")

        # 验证文件格式
        allowed_extensions = {'.xlsx', '.xls'}

        if not Path(last_month_file.filename).suffix.lower() in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"上个月文件格式不支持，仅支持: {', '.join(allowed_extensions)}"
            )

        if not Path(this_month_file.filename).suffix.lower() in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"本月文件格式不支持，仅支持: {', '.join(allowed_extensions)}"
            )

        # 保存上传的文件到临时目录
        temp_last_month = TEMP_DIR / f"last_month_{last_month_file.filename}"
        temp_this_month = TEMP_DIR / f"this_month_{this_month_file.filename}"

        try:
            with open(temp_last_month, "wb") as buffer:
                shutil.copyfileobj(last_month_file.file, buffer)

            with open(temp_this_month, "wb") as buffer:
                shutil.copyfileobj(this_month_file.file, buffer)

            logger.info(f"文件保存成功: {temp_last_month}, {temp_this_month}")

            # 处理生鲜环比数据
            result_df, output_path = process_fresh_food_ratio(
                str(temp_last_month),
                str(temp_this_month),
                output_filename
            )

            # 生成统计信息
            total_customers = len(result_df)
            active_customers_this_month = len(result_df[result_df['本月总日活'] > 0])
            active_customers_last_month = len(result_df[result_df['上月总日活'] > 0])

            total_fresh_sales_this_month = result_df['本月生鲜销售额'].sum()
            total_fresh_sales_last_month = result_df['上月生鲜销售额'].sum()

            avg_daily_active_ratio = result_df['总日活环比'].mean()
            avg_fresh_sales_ratio = result_df['生鲜销售额环比'].mean()

            # 返回处理结果
            return {
                "success": True,
                "message": "生鲜环比数据处理成功",
                "data": {
                    "output_file": output_path,
                    "statistics": {
                        "total_customers": total_customers,
                        "active_customers_this_month": active_customers_this_month,
                        "active_customers_last_month": active_customers_last_month,
                        "total_fresh_sales_this_month": total_fresh_sales_this_month,
                        "total_fresh_sales_last_month": total_fresh_sales_last_month,
                        "avg_daily_active_ratio": round(avg_daily_active_ratio, 2),
                        "avg_fresh_sales_ratio": round(avg_fresh_sales_ratio, 2)
                    },
                    "preview": {
                        "columns": result_df.columns.tolist(),
                        "sample_data": result_df.head(5).to_dict('records')
                    }
                }
            }

        finally:
            # 清理临时文件
            for temp_file in [temp_last_month, temp_this_month]:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.info(f"临时文件已清理: {temp_file}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理生鲜环比数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/download-output/{filename}")
async def download_output_file(filename: str) -> FileResponse:
    """
    下载生成的Excel文件

    Args:
        filename: 文件名

    Returns:
        Excel文件
    """
    try:
        file_path = Path("outputs") / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/list-outputs")
async def list_output_files() -> Dict[str, Any]:
    """
    列出所有可用的输出文件

    Returns:
        文件列表
    """
    try:
        outputs_dir = Path("outputs")
        if not outputs_dir.exists():
            return {"success": True, "files": []}

        files = []
        for file_path in outputs_dir.glob("*.xlsx"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "created_time": stat.st_ctime,
                "download_url": f"/download-output/{file_path.name}"
            })

        # 按创建时间倒序排列
        files.sort(key=lambda x: x["created_time"], reverse=True)

        return {
            "success": True,
            "files": files
        }

    except Exception as e:
        logger.error(f"列出文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")


@router.delete("/delete-output/{filename}")
async def delete_output_file(filename: str) -> Dict[str, Any]:
    """
    删除输出文件

    Args:
        filename: 文件名

    Returns:
        删除结果
    """
    try:
        file_path = Path("outputs") / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        file_path.unlink()
        logger.info(f"文件已删除: {file_path}")

        return {
            "success": True,
            "message": f"文件 {filename} 已成功删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")