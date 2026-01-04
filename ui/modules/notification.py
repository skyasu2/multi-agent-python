"""
Notification Module
"""
import streamlit.components.v1 as components

def trigger_browser_notification(title: str, body: str):
    """
    브라우저 알림(Notification API)을 트리거합니다.
    Streamlit 환경에서 JS를 주입합니다.
    """
    js_code = f"""
    <script>
    (function() {{
        function notify() {{
            if (!("Notification" in window)) {{
                console.log("This browser does not support desktop notification");
                return;
            }}
            
            if (Notification.permission === "granted") {{
                new Notification("{title}", {{ body: "{body}" }});
            }} else if (Notification.permission !== "denied") {{
                Notification.requestPermission().then(function (permission) {{
                    if (permission === "granted") {{
                        new Notification("{title}", {{ body: "{body}" }});
                    }}
                }});
            }}
        }}
        // DOM 로드 안정화 후 실행
        setTimeout(notify, 1000);
    }})();
    </script>
    """
    components.html(js_code, height=0, width=0)
