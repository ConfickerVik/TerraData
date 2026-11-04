import json
from datetime import datetime

def format_timestamp(ts):
    if not ts:
        return "н/д"
    try:
        # Timestamp is in milliseconds
        return datetime.fromtimestamp(ts / 1000.0).strftime('%d.%m.%Y')
    except Exception:
        return str(ts)

class PDFService:
    def generate_report(self, data, output_path):
        """
        Generates a PDF report from the provided data.
        Since we are in the setup phase, this will currently save a text-based 
        summary to simulate the PDF generation until we install fpdf2/reportlab.
        """
        elements = data.get("elements", [])
        if not elements:
            return False
        
        obj = elements[0]
        addr = obj.get("address", {})
        
        report_content = [
            "ОТЧЕТ ОБ ОБЪЕКТЕ НЕДВИЖИМОСТИ",
            "="*30,
            f"Кадастровый номер: {obj.get('cadNumber')}",
            f"Адрес: {addr.get('readableAddress')}",
            f"Площадь: {obj.get('area')} {obj.get('mainCharacters', [{}])[0].get('unitDescription', 'кв.м') if obj.get('mainCharacters') else 'кв.м'}",
            f"Этаж: {obj.get('levelFloor')}",
            f"Кадастровая стоимость: {obj.get('cadCost')} руб.",
            f"Дата оценки: {format_timestamp(obj.get('cadCostDeterminationDate'))}",
            "",
            "ПРАВА СОБСТВЕННОСТИ:",
            "-"*20
        ]
        
        for right in obj.get("rights", []):
            report_content.append(f"- {right.get('rightTypeDesc')}, Рег. дата: {format_timestamp(right.get('rightRegDate'))}, Номер: {right.get('rightNumber')}")
            
        report_content.append("")
        report_content.append("ОБРЕМЕНЕНИЯ:")
        report_content.append("-"*20)
        
        for enc in obj.get("encumbrances", []):
            report_content.append(f"- {enc.get('typeDesc')}, Дата: {format_timestamp(enc.get('startDate'))}, Номер: {enc.get('encumbranceNumber')}")

        full_text = "\n".join(report_content)
        
        # For now, we write to a text file to verify logic. 
        # In the next step, I'll implement real PDF generation.
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        return True
