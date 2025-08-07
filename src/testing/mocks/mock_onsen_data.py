"""
Mock onsen data for testing the scraper functionality.
"""

from typing import Dict, Any


# Sample onsen mapping data (what would be extracted from the main page)
MOCK_ONSEN_MAPPING = {
    "123": "001",
    "456": "002",
    "789": "003",
    "101": "004",
    "202": "005",
}


# Sample raw HTML for onsen list page
MOCK_ONSEN_LIST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Onsen List</title></head>
<body>
    <div id="areaDIV11">
        <div id="areaDIV1">
            <table>
                <tbody>
                    <tr>
                        <td>
                            <div>
                                <table>
                                    <tbody>
                                        <tr>
                                            <td>
                                                <div>
                                                    <span>001</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table>
                                <tbody>
                                    <tr>
                                        <td>
                                            <div onclick="details(123)">温泉名</div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="areaDIV2">
            <table>
                <tbody>
                    <tr>
                        <td>
                            <div>
                                <table>
                                    <tbody>
                                        <tr>
                                            <td>
                                                <div>
                                                    <span>002</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table>
                                <tbody>
                                    <tr>
                                        <td>
                                            <div onclick="details(456)">温泉名2</div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""


# Sample raw HTML for individual onsen page
MOCK_ONSEN_DETAIL_HTML = """
<!DOCTYPE html>
<html>
<head><title>Onsen Detail</title></head>
<body>
    <div>別府温泉 海地獄</div>
    <div>123 別府温泉 海地獄</div>
    <div>
        <iframe src="https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15"></iframe>
    </div>
    <div>
        <table>
            <tbody>
                <tr>
                    <td>住所</td>
                    <td>大分県別府市鉄輪559-1</td>
                </tr>
                <tr>
                    <td>電話</td>
                    <td>0977-66-1577</td>
                </tr>
                <tr>
                    <td>営業形態</td>
                    <td>日帰り入浴</td>
                </tr>
                <tr>
                    <td>入浴料金</td>
                    <td>大人400円、小人200円</td>
                </tr>
                <tr>
                    <td>利用時間</td>
                    <td>8:30～17:00（年中無休）</td>
                </tr>
                <tr>
                    <td>定休日ほか</td>
                    <td>年中無休</td>
                </tr>
                <tr>
                    <td>家族湯(貸切湯)</td>
                    <td>あり（要予約）</td>
                </tr>
                <tr>
                    <td>泉質</td>
                    <td>含硫黄-ナトリウム-塩化物泉</td>
                </tr>
                <tr>
                    <td>最寄バス停</td>
                    <td>海地獄前（徒歩1分）</td>
                </tr>
                <tr>
                    <td>最寄駅(徒歩)</td>
                    <td>別府駅（バス15分）</td>
                </tr>
                <tr>
                    <td>駐車場</td>
                    <td>あり（無料）</td>
                </tr>
                <tr>
                    <td>備考</td>
                    <td>観光地としても人気の温泉施設</td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""


# Sample extracted data (what the scraper would extract)
MOCK_EXTRACTED_ONSEN_DATA = {
    "region": "別府",  # This is the region
    "ban_number": "123",
    "name": "別府温泉 海地獄",
    "latitude": 33.2797,
    "longitude": 131.5011,
    "map_url": "https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15",
    "住所": "大分県別府市鉄輪559-1",
    "電話": "0977-66-1577",
    "営業形態": "日帰り入浴",
    "入浴料金": "大人400円、小人200円",
    "利用時間": "8:30～17:00（年中無休）",
    "定休日ほか": "年中無休",
    "家族湯(貸切湯)": "あり（要予約）",
    "泉質": "含硫黄-ナトリウム-塩化物泉",
    "最寄バス停": "海地獄前（徒歩1分）",
    "最寄駅(徒歩)": "別府駅（バス15分）",
    "駐車場": "あり（無料）",
    "備考": "観光地としても人気の温泉施設",
}


# Sample mapped data (what would be ready for database insertion)
MOCK_MAPPED_ONSEN_DATA = {
    "name": "別府温泉 海地獄",
    "ban_number": "123",
    "region": "別府",
    "latitude": 33.2797,
    "longitude": 131.5011,
    "description": "温泉名: 別府温泉 海地獄 | 泉質: 含硫黄-ナトリウム-塩化物泉 | 営業形態: 日帰り入浴 | 入浴料金: 大人400円、小人200円 | 利用時間: 8:30～17:00（年中無休） | 備考: 観光地としても人気の温泉施設",
    "business_form": "日帰り入浴",
    "address": "大分県別府市鉄輪559-1",
    "phone": "0977-66-1577",
    "admission_fee": "大人400円、小人200円",
    "usage_time": "8:30～17:00（年中無休）",
    "closed_days": "年中無休",
    "private_bath": "あり（要予約）",
    "spring_quality": "含硫黄-ナトリウム-塩化物泉",
    "nearest_bus_stop": "海地獄前（徒歩1分）",
    "nearest_station": "別府駅（バス15分）",
    "parking": "あり（無料）",
    "remarks": "観光地としても人気の温泉施設",
}


# Sample complete scraped onsen entry
MOCK_COMPLETE_ONSEN_ENTRY = {
    "onsen_id": "123",
    "url": "https://onsen-hunter.oita-apc.co.jp/dhunter/details_onsen.jsp?d=f8a23e58-f16b-4bb0-8b22-2e6acc46c5d5&o=onsendo&e=onsendo&f=list_onsen.jsp%3Fd%3Df8a23e58-f16b-4bb0-8b22-2e6acc46c5d5%26o%3Donsendo%26e%3Donsendo&t=123",
    "raw_html": MOCK_ONSEN_DETAIL_HTML,
    "extracted_data": MOCK_EXTRACTED_ONSEN_DATA,
    "mapped_data": MOCK_MAPPED_ONSEN_DATA,
    "mapping_summary": {
        "total_fields": 18,
        "filled_fields": 18,
        "required_fields_present": True,
        "has_coordinates": True,
        "table_entries_mapped": 12,
    },
}


# Sample error response
MOCK_ERROR_ONSEN_ENTRY = {
    "onsen_id": "999",
    "url": "https://onsen-hunter.oita-apc.co.jp/dhunter/details_onsen.jsp?d=f8a23e58-f16b-4bb0-8b22-2e6acc46c5d5&o=onsendo&e=onsendo&f=list_onsen.jsp%3Fd%3Df8a23e58-f16b-4bb0-8b22-2e6acc46c5d5%26o%3Donsendo%26e%3Donsendo&t=999",
    "error": "Page not found",
    "extracted_data": {},
}


# Sample incomplete data for testing edge cases
MOCK_INCOMPLETE_ONSEN_DATA = {
    "region": "大分",  # This is the region
    "ban_number": "456",
    "name": "テスト温泉",
    "latitude": None,
    "longitude": None,
    "map_url": "",
    "住所": "大分県大分市テスト町1-1",
    "電話": "097-123-4567",
    # Missing other fields
}


# Sample data with different region
MOCK_YUFUIN_ONSEN_DATA = {
    "region": "湯布院",  # This is the region
    "ban_number": "789",
    "name": "湯布院温泉 金鱗湖",
    "latitude": 33.2633,
    "longitude": 131.3544,
    "map_url": "https://maps.google.co.jp/maps?q=33.2633,131.3544&z=15",
    "住所": "大分県由布市湯布院町川上",
    "電話": "0977-85-2323",
    "営業形態": "日帰り入浴",
    "入浴料金": "大人500円",
    "利用時間": "6:00～22:00",
    "定休日ほか": "年中無休",
    "家族湯(貸切湯)": "なし",
    "泉質": "単純温泉",
    "最寄バス停": "金鱗湖前",
    "最寄駅(徒歩)": "由布院駅（徒歩15分）",
    "駐車場": "あり（有料）",
    "備考": "金鱗湖の美しい景色を楽しめる温泉",
}


def get_mock_onsen_mapping() -> Dict[str, str]:
    """Get mock onsen mapping data."""
    return MOCK_ONSEN_MAPPING.copy()


def get_mock_extracted_data() -> Dict[str, Any]:
    """Get mock extracted onsen data."""
    return MOCK_EXTRACTED_ONSEN_DATA.copy()


def get_mock_mapped_data() -> Dict[str, Any]:
    """Get mock mapped onsen data."""
    return MOCK_MAPPED_ONSEN_DATA.copy()


def get_mock_complete_entry() -> Dict[str, Any]:
    """Get mock complete onsen entry."""
    return MOCK_COMPLETE_ONSEN_ENTRY.copy()


def get_mock_error_entry() -> Dict[str, Any]:
    """Get mock error onsen entry."""
    return MOCK_ERROR_ONSEN_ENTRY.copy()


def get_mock_incomplete_data() -> Dict[str, Any]:
    """Get mock incomplete onsen data."""
    return MOCK_INCOMPLETE_ONSEN_DATA.copy()


def get_mock_yufuin_data() -> Dict[str, Any]:
    """Get mock Yufuin onsen data."""
    return MOCK_YUFUIN_ONSEN_DATA.copy()


def get_mock_onsen_list_html() -> str:
    """Get mock onsen list HTML."""
    return MOCK_ONSEN_LIST_HTML


def get_mock_onsen_detail_html() -> str:
    """Get mock onsen detail HTML."""
    return MOCK_ONSEN_DETAIL_HTML
