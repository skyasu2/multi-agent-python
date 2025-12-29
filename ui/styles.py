
CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 4rem;
        padding-bottom: 8rem;
    }

    .result-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .stButton > button {
        padding: 0.3rem 0.8rem;
        font-size: 0.9rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        border-color: #667eea;
        color: #667eea;
        background-color: #f0f4ff;
    }

    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem 1rem 2rem 1rem;
        background: linear-gradient(to top, #ffffff 90%, rgba(255,255,255,0));
        z-index: 1000;
        border-top: none;
    }

    .stChatInput > div {
        max-width: 800px;
        margin: 0 auto;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-radius: 28px;
    }

    .stChatInput textarea {
        border-radius: 28px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 14px 24px !important;
        font-size: 1rem !important;
        background-color: #ffffff !important;
    }

    .stChatInput textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    
    .stChatInput div[data-baseweb="textarea"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    .stChatInput div[data-baseweb="base-input"] {
         background-color: transparent !important;
    }

    .stChatInput button[kind="primary"] {
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        right: 10px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
    }

    .stChatInput button[kind="primary"]:hover {
        opacity: 0.9;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    
    .stChatInput button[kind="primary"] svg {
        width: 18px !important;
        height: 18px !important;
    }

    /* Green Download Button */
    div[data-testid="stDownloadButton"] button {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        transition: transform 0.2s;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #218838 !important;
        transform: scale(1.02);
        color: white !important;
    }

    /* Bounce Animation */
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
        40% {transform: translateY(-10px);}
        60% {transform: translateY(-5px);}
    }
    .bounce-guide {
        animation: bounce 1.5s infinite;
        text-align: center;
        color: #28a745;
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 1.1em;
    }
</style>
"""
