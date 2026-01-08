"""
UI Components Module (Facade)

This module re-exports components extracted into `ui/modules/`.
This ensures backward compatibility while the codebase is refactored into modular components.
"""
import streamlit as st
import streamlit.components.v1 as components

# Re-export modules
from ui.modules.mermaid import (
    render_scalable_mermaid, 
    render_mermaid, 
    render_markdown_with_mermaid
)
from ui.modules.progress import (
    render_visual_timeline, 
    render_progress_steps, 
    render_specialist_agents_status, 
    render_timeline
)
from ui.modules.chat import render_chat_message, render_chat_history
from ui.modules.interaction import (
    render_error_state, 
    render_human_interaction, 
    render_option_selector
)
from ui.modules.notification import trigger_browser_notification
from ui.modules.badges import render_plan_badges

# [Compatibility Note]
# If any newly created module needs to access shared styles or constants,
# those should be extracted to `ui/modules/styles.py` or similar.
