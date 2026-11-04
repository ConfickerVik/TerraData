import os
import uuid
import threading
import httpx
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pdfkit
from typing import Optional, Dict, Any

class RosreestrPdfConverter:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            # Path relative to the project root: app/models/pred.keras
            # This file is in app/services/, so we go up two levels to reach root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_path = os.path.join(base_dir, 'app', 'models', 'pred.keras')
        
        self.max_tries = 20
        self.sessions = {}
        self.sessions_lock = threading.Lock()
        
        # Load Model
        try:
            self.model = keras.models.load_model(model_path)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

        # OCR Characters
        self.characters = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'а', 'б', 'в', 'г', 'д', 'е', 'и', 'к', 'л', 'м', 'н', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ч', 'э', 'я']
        self.char_to_num = layers.StringLookup(vocabulary=list(self.characters), mask_token=None)
        self.num_to_char = layers.StringLookup(vocabulary=self.char_to_num.get_vocabulary(), mask_token=None, invert=True)

    def _encode_single_sample(self, img_path):
        img = tf.io.read_file(img_path)
        img = tf.io.decode_png(img, channels=1)
        img = tf.image.convert_image_dtype(img, tf.float32)
        img = tf.transpose(img, perm=[1, 0, 2])
        return {"image": img}

    def _decode_batch_predictions(self, pred):
        input_len = np.ones(pred.shape[0]) * pred.shape[1]
        results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :5]
        output_text = []
        for res in results:
            res_text = tf.strings.reduce_join(self.num_to_char(res)).numpy().decode("utf-8")
            output_text.append(res_text)
        return output_text

    def solve_captcha(self, captcha_path: str) -> Optional[str]:
        if self.model is None:
            return None
        
        try:
            dataset = tf.data.Dataset.from_tensor_slices([captcha_path])
            dataset = dataset.map(self._encode_single_sample).batch(1)
            
            for batch in dataset.take(1):
                preds = self.model.predict(batch["image"], verbose=0)
                pred_texts = self._decode_batch_predictions(preds)
                return pred_texts[0]
        except Exception as e:
            print(f"Captcha solve error: {e}")
            return None

    def convert_xml_to_pdf(self, xml_data: bytes) -> bytes:
        """
        Main method to convert XML to PDF using Rosreestr LK.
        """
        temp_xml_path = f"temp_{uuid.uuid4()}.xml"
        with open(temp_xml_path, "wb") as f:
            f.write(xml_data)

        session = httpx.Client(verify=False)
        try:
            statement_guid = str(uuid.uuid4())
            
            # 1. Solve Captcha & Upload
            captcha_solved = False
            for i in range(self.max_tries):
                try:
                    resp = session.get("https://lk.rosreestr.ru/account-back/captcha.png")
                    captcha_path = f"captcha_{statement_guid}.png"
                    with open(captcha_path, "wb") as f:
                        f.write(resp.content)
                    
                    captcha_text = self.solve_captcha(captcha_path)
                    if not captcha_text: continue

                    payload = {"statementGuid": statement_guid, "captcha": captcha_text}
                    with open(temp_xml_path, 'rb') as f:
                        files = {'file': f}
                        upload_resp = session.post("https://lk.rosreestr.ru/account-back/check-doc/uploadFile", data=payload, files=files)
                        
                    if upload_resp.status_code == 200:
                        captcha_solved = True
                        os.remove(captcha_path)
                        break
                except Exception as e:
                    print(f"Upload attempt {i} failed: {e}")

            if not captcha_solved:
                raise Exception("Failed to solve captcha and upload file after max tries")

            # 2. Trigger Check
            check_success = False
            payload = {
                "statementGuid": statement_guid,
                "captcha": captcha_text,
                "xmlFile": os.path.basename(temp_xml_path),
                "sigFile": "",
                "justSignatureCheck": False,
            }
            
            for i in range(self.max_tries):
                try:
                    check_resp = session.post("https://lk.rosreestr.ru/account-back/check-doc/check", json=payload)
                    if check_resp.status_code == 200:
                        if check_resp.json().get("transformStatus") == "ERROR":
                            raise Exception("Rosreestr transform error")
                        check_success = True
                        break
                except Exception as e:
                    print(f"Check attempt {i} failed: {e}")

            if not check_success:
                raise Exception("Failed to trigger document check")

            # 3. Get HTML and convert to PDF
            html_content = None
            for i in range(self.max_tries):
                try:
                    view_resp = session.get(f"https://lk.rosreestr.ru/account-back/check-doc/view/{statement_guid}")
                    if view_resp.status_code == 200:
                        html_content = view_resp.text
                        break
                except Exception as e:
                    print(f"View attempt {i} failed: {e}")

            if not html_content:
                raise Exception("Failed to retrieve document HTML")

            # 4. PDF conversion
            pdf_bytes = pdfkit.from_string(html_content, False)
            
            # Cleanup Rosreestr side
            try:
                session.delete(f"https://lk.rosreestr.ru/account-back/check-doc/delete/{statement_guid}")
                session.delete(f"https://lk.rosreestr.ru/account-back/check-doc/delete-sig/{statement_guid}")
            except:
                pass
                
            return pdf_bytes

        finally:
            session.close()
            if os.path.exists(temp_xml_path):
                os.remove(temp_xml_path)
