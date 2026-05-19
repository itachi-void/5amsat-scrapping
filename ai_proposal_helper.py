import json
import logging
import requests

logger = logging.getLogger(__name__)

class AIProposalHelper:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def is_configured(self):
        return bool(self.api_key)

    def _call_gemini(self, prompt, schema=None):
        if not self.api_key:
            return None
        
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3
            }
        }
        
        if schema:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            
        try:
            r = requests.post(f"{self.url}", params=params, json=payload, headers=headers, timeout=20)
            if r.status_code == 200:
                resp_json = r.json()
                text = resp_json['candidates'][0]['content']['parts'][0]['text']
                return text
            else:
                logger.error(f"Gemini API returned status code {r.status_code}: {r.text}")
                return None
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None

    def score_project(self, title, description, profile):
        prompt = f"""
You are an expert freelancer matching assistant.
Analyze the following project description from Mostaql/Khamsat freelancing platform:
Title: {title}
Description: {description}

Freelancer Profile:
{profile}

Assess the compatibility of this project with the freelancer's profile.
Return a JSON object with the following schema:
{{
  "score_category": "High" | "Medium" | "Low",
  "score_percentage": 92,
  "reason": "concise explanation in Arabic justifying the score"
}}
Do not return any other text, only the raw JSON.
"""
        raw_resp = self._call_gemini(prompt, schema=True)
        if not raw_resp:
            return None
            
        try:
            cleaned = raw_resp.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Failed to parse score_project JSON: {e}. Raw response: {raw_resp}")
            return None

    def draft_proposal(self, title, description, profile, portfolio):
        prompt = f"""
You are an expert copywriter and freelancer bidding assistant.
Write a professional, highly personalized proposal (in Arabic) for the following project:
Title: {title}
Description: {description}

Freelancer Profile:
{profile}

Portfolio Links:
{portfolio}

Guidelines:
1. Start with a direct, custom introduction that addresses the client's specific problem. NEVER use generic openings like "قرأت طلبك وجاهز للتنفيذ".
2. Explain briefly how you will solve their problem (steps or tech stack).
3. Insert 1 or 2 relevant portfolio links from the list. Choose the best ones. Do not list more than 2.
4. Keep the tone professional, friendly, and natural (as if a human wrote it, not a bot).
5. End with a clear call to action (e.g., asking a question about the project or inviting them to discuss details).
6. Keep the proposal concise (max 3-4 paragraphs).

Return a JSON object with the following schema:
{{
  "proposal_text": "the generated proposal in Arabic",
  "budget": 150,
  "duration": 4
}}
The "budget" and "duration" must be integers. Suggest a realistic budget in USD.
Do not return any other text, only the raw JSON.
"""
        raw_resp = self._call_gemini(prompt, schema=True)
        if not raw_resp:
            return None
            
        try:
            cleaned = raw_resp.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Failed to parse draft_proposal JSON: {e}. Raw response: {raw_resp}")
            return None
