import os
import json
import uuid
import logging
import requests
import threading
from ai_proposal_helper import AIProposalHelper
from hsoub_bidder import HsoubBidder

logger = logging.getLogger(__name__)

class AutobidManager:
    def __init__(self, bot_type="khamsat", data_dir="."):
        self.bot_type = bot_type
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, f"{bot_type}_autobid_config.json")
        self.bids_file = os.path.join(data_dir, f"{bot_type}_pending_bids.json")
        self.states_file = os.path.join(data_dir, f"{bot_type}_user_states.json")
        
        self.config = self._load_json(self.config_file, {
            "enabled": False,
            "gemini_api_key": "",
            "freelancer_profile": "مطور بايثون محترف خبير في كشط البيانات وأتمتة العمليات وبناء بوتات تليجرام وتطوير الويب.",
            "portfolio_links": []
        })
        
        self.pending_bids = self._load_json(self.bids_file, {})
        self.user_states = self._load_json(self.states_file, {})
        
        # Initialize helpers
        api_key = self.config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        self.ai_helper = AIProposalHelper(api_key=api_key)
        self.bidder = HsoubBidder(data_dir=data_dir)

    def _load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")
        return default

    def _save_json(self, path, data):
        tmp = path + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(tmp, path)
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")

    def save_config(self):
        self._save_json(self.config_file, self.config)
        api_key = self.config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        self.ai_helper.api_key = api_key

    def save_bids(self):
        self._save_json(self.bids_file, self.pending_bids)

    def save_states(self):
        self._save_json(self.states_file, self.user_states)

    def set_user_state(self, chat_id, state, meta=None):
        self.user_states[str(chat_id)] = {"state": state, "meta": meta or {}}
        self.save_states()

    def clear_user_state(self, chat_id):
        self.user_states.pop(str(chat_id), None)
        self.save_states()

    def get_user_state(self, chat_id):
        return self.user_states.get(str(chat_id))

    def evaluate_project(self, title, desc, link=None):
        if not self.config.get("enabled"):
            return None
            
        gemini_key = self.config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            logger.warning("Gemini API key is not configured for auto-bid evaluation.")
            return None
            
        self.ai_helper.api_key = gemini_key
        
        # Step 1: Score
        score_res = self.ai_helper.score_project(title, desc, self.config["freelancer_profile"])
        if not score_res:
            return None
            
        category = score_res.get("score_category", "Low")
        percentage = score_res.get("score_percentage", 0)
        reason = score_res.get("reason", "")
        
        if category in ("High", "Medium"):
            # Step 2: Draft Proposal
            portfolio_str = "\n".join(self.config.get("portfolio_links", []))
            draft_res = self.ai_helper.draft_proposal(title, desc, self.config["freelancer_profile"], portfolio_str)
            if draft_res:
                bid_id = f"bid_{uuid.uuid4().hex[:8]}"
                bid_data = {
                    "id": bid_id,
                    "title": title,
                    "desc": desc,
                    "link": link,
                    "proposal_text": draft_res.get("proposal_text", ""),
                    "budget": draft_res.get("budget", 5), # khamsat default
                    "duration": draft_res.get("duration", 1),
                    "score_category": category,
                    "score_percentage": percentage,
                    "reason": reason
                }
                self.pending_bids[bid_id] = bid_data
                self.save_bids()
                return bid_data
                
        return {
            "score_category": category,
            "score_percentage": percentage,
            "reason": reason,
            "no_draft": True
        }

    def generate_admin_menu(self, chat_id):
        enabled_status = "🟢 نشط" if self.config.get("enabled") else "🔴 معطل"
        key_status = "🟢 متصل" if (self.config.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")) else "🔴 غير متصل"
        
        menu_text = (
            f"🤖 **لوحة تحكم نظام التقديم التلقائي الذكي ({self.bot_type.capitalize()}):**\n\n"
            f"• حالة النظام: {enabled_status}\n"
            f"• مفتاح Gemini: {key_status}\n"
            f"• المتصفح (Playwright): {'🟢 متوفر' if self.bidder.is_available() else '🔴 غير متوفر'}\n\n"
            "💬 **الخيارات المتاحة:**\n"
            "1. تشغيل أو إيقاف ميزة كشف وتقييم المشاريع تلقائياً.\n"
            "2. تحديث مفتاح Gemini API Key لتوليد العروض.\n"
            "3. تعديل ملف الخبرات الخاص بك (الـ Resume prompt) الممرر للـ AI.\n"
            "4. إدارة روابط معرض أعمالك المرفقة بالعروض.\n"
            "5. تسجيل الدخول بالمتصفح (فتح نافذة Headed يدوية لحفظ الجلسة).\n"
            "6. فحص حالة الاتصال النشطة بالمنصة حالياً."
        )
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🟢 تشغيل" if not self.config.get("enabled") else "🔴 إيقاف", "callback_data": "autobid:toggle"},
                    {"text": "🔑 مفتاح Gemini", "callback_data": "autobid:set_key"}
                ],
                [
                    {"text": "👨‍💼 ملف الخبرات", "callback_data": "autobid:edit_profile"},
                    {"text": "🔗 معرض الأعمال", "callback_data": "autobid:edit_portfolio"}
                ],
                [
                    {"text": "🔑 تسجيل دخول (Headed)", "callback_data": "autobid:login_headed"},
                    {"text": "🔍 فحص الجلسة", "callback_data": "autobid:check_session"}
                ],
                [
                    {"text": "🔙 لوحة التحكم الرئيسية", "callback_data": "backup_op:back_to_menu"}
                ]
            ]
        }
        return menu_text, keyboard

    def send_evaluation_card(self, chat_id, bid_data, project_link, base_url):
        msg_text = (
            f"🤖 **[تجربة التقديم التلقائي - {self.bot_type.capitalize()}]**\n\n"
            f"📝 **المشروع:** {bid_data['title']}\n"
            f"📊 **التقييم:** {bid_data['score_category']} ({bid_data['score_percentage']}%)\n"
            f"🧐 **السبب:** {bid_data['reason']}\n\n"
            f"✍️ **العرض المقترح:**\n"
            f"\"{bid_data['proposal_text']}\"\n\n"
            f"🔗 **رابط المشروع:** [اضغط هنا للفتح]({project_link})"
        )
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "⚡ إرسال العرض", "callback_data": f"autobid:send_{bid_data['id']}"},
                    {"text": "📝 تعديل", "callback_data": f"autobid:edit_{bid_data['id']}"}
                ],
                [
                    {"text": "❌ تخطي", "callback_data": f"autobid:skip_{bid_data['id']}"}
                ]
            ]
        }
        
        requests.post(f"{base_url}/sendMessage", json={
            "chat_id": chat_id,
            "text": msg_text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        })

    def handle_callback(self, chat_id, data, callback_id, base_url):
        if data == "autobid:toggle":
            self.config["enabled"] = not self.config.get("enabled", False)
            self.save_config()
            status = "نشط" if self.config["enabled"] else "معطل"
            requests.post(f"{base_url}/answerCallbackQuery", json={
                "callback_query_id": callback_id,
                "text": f"✅ تم تعديل الحالة إلى: {status}",
                "show_alert": True
            })
            return True
            
        elif data == "autobid:set_key":
            self.set_user_state(chat_id, "waiting_for_gemini_key")
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": "🔑 الرجاء إرسال مفتاح Gemini API Key الجديد الآن:"
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            return True
            
        elif data == "autobid:edit_profile":
            self.set_user_state(chat_id, "waiting_for_profile")
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": (
                    f"👨‍💼 **ملف الخبرات الحالي:**\n\n`{self.config.get('freelancer_profile')}`\n\n"
                    "قم بالرد على هذه الرسالة أو أرسل النص الجديد بالكامل لتحديثه:"
                )
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            return True
            
        elif data == "autobid:edit_portfolio":
            self.set_user_state(chat_id, "waiting_for_portfolio")
            links = self.config.get("portfolio_links", [])
            links_str = "\n".join([f"- {l}" for l in links]) if links else "لا يوجد روابط مسجلة حالياً."
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": (
                    f"🔗 **روابط معرض أعمالك الحالي:**\n\n{links_str}\n\n"
                    "لتحديث القائمة، أرسل الروابط الجديدة الآن (رابط في كل سطر):\n"
                    "💡 أرسل كلمة `clear` لمسح كل الروابط."
                )
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            return True
            
        elif data == "autobid:login_headed":
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"⏳ جاري تشغيل المتصفح المرئي على السيرفر لتسجيل الدخول إلى {self.bot_type.capitalize()}..."
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            
            def run_login():
                ok, msg = self.bidder.run_login_session(site=self.bot_type)
                requests.post(f"{base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": f"{'✅' if ok else '❌'} نتيجة تسجيل الدخول:\n{msg}"
                })
            threading.Thread(target=run_login, daemon=True).start()
            return True
            
        elif data == "autobid:check_session":
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"🔍 جاري فحص حالة جلسة تسجيل الدخول في الخلفية..."
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            
            def run_check():
                ok, msg = self.bidder.check_session_status(site=self.bot_type)
                requests.post(f"{base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": f"{'🟢 الجلسة نشطة وتعمل!' if ok else '🔴 الجلسة منتهية أو لم يتم تسجيل الدخول.'}\nتفاصيل: {msg}"
                })
            threading.Thread(target=run_check, daemon=True).start()
            return True

        elif data.startswith("autobid:send_"):
            bid_id = data.split("autobid:send_", 1)[1]
            bid_data = self.pending_bids.get(bid_id)
            if not bid_data:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": "⚠️ لم يتم العثور على العرض المخصص، قد يكون تم حذفه أو تخطيه.", "show_alert": True})
                return True
                
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": "⏳ جاري إرسال العرض في الخلفية عبر Playwright..."
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            
            def run_submit():
                proj_link = bid_data.get("link") or f"https://khamsat.com/community/requests/{bid_data['id'].split('_', 1)[1]}"
                
                ok, msg, screenshot_path = self.bidder.submit_bid(
                    site=self.bot_type,
                    project_url=proj_link,
                    proposal_text=bid_data["proposal_text"]
                )
                
                if ok:
                    requests.post(f"{base_url}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": f"✅ تم إرسال الرد بنجاح على الطلب:\n*{bid_data['title']}*",
                        "parse_mode": "Markdown"
                    })
                    self.pending_bids.pop(bid_id, None)
                    self.save_bids()
                else:
                    requests.post(f"{base_url}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": f"❌ فشل إرسال الرد:\n{msg}"
                    })
                    if screenshot_path and os.path.exists(screenshot_path):
                        try:
                            with open(screenshot_path, 'rb') as f:
                                requests.post(
                                    f"{base_url}/sendPhoto",
                                    data={"chat_id": chat_id, "caption": "📸 لقطة شاشة للخطأ أثناء التقديم"},
                                    files={"photo": f},
                                    timeout=20
                                )
                        except Exception as e:
                            logger.error(f"Failed to send error screenshot: {e}")
                            
            threading.Thread(target=run_submit, daemon=True).start()
            return True
            
        elif data.startswith("autobid:skip_"):
            bid_id = data.split("autobid:skip_", 1)[1]
            self.pending_bids.pop(bid_id, None)
            self.save_bids()
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": "❌ تم تخطي الطلب وحذف العرض المقترح.", "show_alert": True})
            return True

        elif data.startswith("autobid:edit_"):
            bid_id = data.split("autobid:edit_", 1)[1]
            bid_data = self.pending_bids.get(bid_id)
            if not bid_data:
                requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": "⚠️ العرض غير موجود.", "show_alert": True})
                return True
                
            menu_text = (
                f"📝 **تعديل رد طلب:** {bid_data['title']}\n\n"
                "اختر الإجراء الذي ترغب به:"
            )
            
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "✍️ تعديل النص", "callback_data": f"autobid:edittext_{bid_id}"},
                        {"text": "🔙 عودة للبطاقة", "callback_data": f"autobid:show_{bid_id}"}
                    ]
                ]
            }
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": menu_text,
                "reply_markup": keyboard
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            return True
            
        elif data.startswith("autobid:show_"):
            bid_id = data.split("autobid:show_", 1)[1]
            bid_data = self.pending_bids.get(bid_id)
            if bid_data:
                proj_link = bid_data.get("link") or f"https://khamsat.com/community/requests/{bid_data['id'].split('_', 1)[1]}"
                self.send_evaluation_card(chat_id, bid_data, proj_link, base_url)
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            return True

        elif data.startswith("autobid:edittext_"):
            bid_id = data.split("autobid:edittext_", 1)[1]
            self.set_user_state(chat_id, "waiting_for_bid_text", {"bid_id": bid_id})
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": "✍️ حسناً، قم بالرد (Reply) على هذه الرسالة بنص الرد المعدل الجديد بالكامل:"
            })
            requests.post(f"{base_url}/answerCallbackQuery", json={"callback_query_id": callback_id})
            return True

        return False

    def handle_reply(self, chat_id, text, base_url):
        state_data = self.get_user_state(chat_id)
        if not state_data:
            return False
            
        state = state_data.get("state")
        meta = state_data.get("meta", {})
        
        if state == "waiting_for_gemini_key":
            self.config["gemini_api_key"] = text.strip()
            self.save_config()
            self.clear_user_state(chat_id)
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": "✅ تم تحديث مفتاح Gemini API Key بنجاح!"
            })
            return True
            
        elif state == "waiting_for_profile":
            self.config["freelancer_profile"] = text.strip()
            self.save_config()
            self.clear_user_state(chat_id)
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": "✅ تم تحديث ملف الخبرات والـ Resume prompt بنجاح!"
            })
            return True
            
        elif state == "waiting_for_portfolio":
            val = text.strip()
            if val.lower() == "clear":
                self.config["portfolio_links"] = []
            else:
                self.config["portfolio_links"] = [l.strip() for l in val.split("\n") if l.strip()]
            self.save_config()
            self.clear_user_state(chat_id)
            requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": "✅ تم تحديث روابط معرض الأعمال بنجاح!"
            })
            return True
            
        elif state == "waiting_for_bid_text":
            bid_id = meta.get("bid_id")
            bid_data = self.pending_bids.get(bid_id)
            if bid_data:
                bid_data["proposal_text"] = text.strip()
                self.save_bids()
                self.clear_user_state(chat_id)
                requests.post(f"{base_url}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "✅ تم تعديل نص الرد بنجاح! إليك البطاقة المحدثة:"
                })
                proj_link = bid_data.get("link") or f"https://khamsat.com/community/requests/{bid_data['id'].split('_', 1)[1]}"
                self.send_evaluation_card(chat_id, bid_data, proj_link, base_url)
            else:
                self.clear_user_state(chat_id)
                requests.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": "⚠️ العرض غير موجود."})
            return True
            
        return False
