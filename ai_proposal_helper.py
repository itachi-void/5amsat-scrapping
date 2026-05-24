import json
import logging
import requests

logger = logging.getLogger(__name__)

class AIProposalHelper:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def is_configured(self):
        return bool(self.api_key)

    def _call_gemini(self, prompt):
        if not self.api_key:
            logger.error("No Gemini API key")
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800}
        }
        try:
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                return r.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                logger.error(f"Gemini API error {r.status_code}: {r.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Exception in Gemini call: {e}")
            return None

    def score_project(self, title, description, profile):
        if not description or len(description.strip()) < 10:
            return {"score_category": "Low", "score_percentage": 10, "reason": "وصف الطلب قصير جداً"}
        
        prompt = f"""أنت خبير تقييم مشاريع. قيم التوافق بين المشروع والملف الشخصي للمستقل.
أعد JSON فقط بهذا الشكل:
{{"score_category": "High/Medium/Low", "score_percentage": 0-100, "reason": "سبب التقييم بالعربية"}}
عنوان المشروع: {title}
وصف المشروع: {description}
الملف الشخصي: {profile}"""
        
        resp = self._call_gemini(prompt)
        if not resp:
            return None
        try:
            clean = resp.strip().replace('```json', '').replace('```', '')
            return json.loads(clean)
        except:
            return {"score_category": "Low", "score_percentage": 20, "reason": "فشل تحليل الطلب"}

    def draft_proposal(self, title, description, profile, portfolio):
        if not description or len(description.strip()) < 10:
            return None
        
        prompt = f"""اكتب عرضاً احترافياً قصيراً بالعربية لهذا المشروع (3 فقرات كحد أقصى).
أعد JSON فقط:
{{"proposal_text": "نص العرض", "budget": 150, "duration": 4}}
العنوان: {title}
الوصف: {description}
الملف الشخصي: {profile}
أعمال سابقة: {portfolio}"""
        
        resp = self._call_gemini(prompt)
        if not resp:
            return None
        try:
            clean = resp.strip().replace('```json', '').replace('```', '')
            return json.loads(clean)
        except:
            return {
                "proposal_text": "مرحباً، يمكنني تنفيذ مشروعك بخبرتي في المجال. تواصل معي لمناقشة التفاصيل.",
                "budget": 100,
                "duration": 3
            }
