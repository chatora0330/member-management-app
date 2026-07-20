import jaconv
import re
from fugashi import Tagger

tagger = Tagger()

def get_yomi(text):
    words = tagger(text)
    yomi = ""
    
    for w in words:
        kana = w.feature.kana or w.surface
        yomi += kana
        
    return jaconv.kata2hira(yomi)  # カタカナ → ひらがな変換


def format_phone(phone):
    phone = re.sub(r"\D", "", phone)

    # 携帯電話
    if re.match(r"^0[789]0\d{8}$", phone):
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"

    # 東京・大阪
    elif phone.startswith(("03", "06")) and len(phone) == 10:
        return f"{phone[:2]}-{phone[2:6]}-{phone[6:]}"

    # その他の10桁固定電話
    elif len(phone) == 10:
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"

    return phone