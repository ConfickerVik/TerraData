from fastapi import APIRouter, HTTPException, Query

from app.services.rosreestr_client import RosreestrClient
from app.services.rosreestr_converter import RosreestrPdfConverter

router = APIRouter(prefix="/rosreestr", tags=["Rosreestr Data"])

# We share the converter for captcha solving
converter = RosreestrPdfConverter()
client = RosreestrClient(pdf_converter=converter)


@router.get("/info")
async def get_property_info(cad_num: str):
    """
    Get full raw information about a property by its cadastral number.
    """
    data = await client.get_full_info(cad_num)
    if not data:
        raise HTTPException(
            status_code=404, detail="Property information not found or Rosreestr error"
        )
    return data


@router.get("/search-address")
async def search_address(address: str = Query(..., description="Full address to search for")):
    """
    Search for cadastral numbers by address.
    """
    data = await client.search_by_address(address)
    if not data:
        raise HTTPException(status_code=404, detail="No properties found for this address")
    return data
