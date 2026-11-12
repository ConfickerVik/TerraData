from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.pdf_service import PDFService
from app.services.report_service import ReportService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

report_service = ReportService()
pdf_service = PDFService()


class ReportRequest(BaseModel):
    cad_num: str = Field(..., description="Кадастровый номер объекта")
    include_nspd: bool = Field(True, description="Включить данные НСПД")
    include_fias: bool = Field(True, description="Включить данные ФИАС")
    include_sudrf: bool = Field(True, description="Включить данные СУДРФ")


@router.post("/generate-report")
async def generate_report(request: ReportRequest):
    """
    Генерирует аналитический PDF-отчёт об объекте недвижимости,
    объединяющий данные из Росреестра, НСПД, ФИАС и СУДРФ.
    """
    report = await report_service.gather_report(
        cad_num=request.cad_num,
        include_nspd=request.include_nspd,
        include_fias=request.include_fias,
        include_sudrf=request.include_sudrf,
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Не удалось получить данные об объекте из Росреестра",
        )

    pdf_bytes = pdf_service.generate_report(report)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{request.cad_num}.pdf"},
    )
