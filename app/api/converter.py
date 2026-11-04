from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.rosreestr_converter import RosreestrPdfConverter
import os

router = APIRouter(prefix="/converter", tags=["PDF Converter"])

# Initialize converter (Ideally this should be a dependency injected via FastAPI)
converter = RosreestrPdfConverter()

@router.post("/xml-to-pdf")
async def convert_xml(file: UploadFile = File(...)):
    """
    Uploads an XML file and converts it to an official Rosreestr PDF.
    """
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="File must be an XML document")
    
    try:
        xml_content = await file.read()
        pdf_bytes = converter.convert_xml_to_pdf(xml_content)
        
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=converted_{file.filename}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
